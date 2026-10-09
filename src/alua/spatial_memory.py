from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Any

from .navigation import LocalNavigator
from .perception import PerceptionFrame
from .store import Store
from .topology import perceptual_place_signature
from .world_model import EgocentricWorldModel


def _normalize_angle(value: float) -> float:
    while value > math.pi:
        value -= 2 * math.pi
    while value < -math.pi:
        value += 2 * math.pi
    return value


def _inverse_maneuver(maneuver: str) -> str:
    return {
        "forward": "back",
        "back": "forward",
        "left": "right",
        "right": "left",
    }.get(maneuver, "back")


@dataclass(slots=True)
class RouteStep:
    origin: str
    destination: str
    departure_heading: float
    maneuver: str
    inverse_maneuver: str
    sequence: int


@dataclass(frozen=True, slots=True)
class SpatialDirective:
    kind: str
    reason: str
    yaw_delta_rad: float = 0.0
    maneuver: str | None = None
    target_place: str | None = None
    confidence: float = 0.0


class SpatialMemory:
    """Session-local route memory over perceptual places.

    It stores only self-derived perceptual signatures and relative orientation.
    No absolute World coordinates are used.
    """

    def __init__(self, route_capacity: int = 128) -> None:
        self.route_capacity = max(16, int(route_capacity))
        self.heading_rad = 0.0
        self.pose_x = 0.0
        self.pose_z = 0.0
        self.pose_uncertainty = 0.05
        self.current_place: str | None = None
        self._route: list[RouteStep] = []
        self._failed_moves: dict[str, int] = {}
        self._visits: dict[str, int] = {}
        self._pending_action: dict[str, Any] | None = None
        self._pending_origin: str | None = None
        self._pending_heading: float = 0.0
        self._backtracking = False
        self._backtrack_attempts = 0
        self._backtrack_attempt_limit = 8

    def reset_session(self) -> None:
        self.heading_rad = 0.0
        self.pose_x = 0.0
        self.pose_z = 0.0
        self.pose_uncertainty = 0.05
        self.current_place = None
        self._route.clear()
        self._failed_moves.clear()
        self._visits.clear()
        self._pending_action = None
        self._pending_origin = None
        self._pending_heading = 0.0
        self._backtracking = False
        self._backtrack_attempts = 0

    def observe(
        self,
        frame: PerceptionFrame,
        store: Store | None = None,
        agent_id: str | None = None,
    ) -> str:
        signature = perceptual_place_signature(frame)
        self.current_place = signature
        self._visits[signature] = self._visits.get(signature, 0) + 1
        if store is not None and agent_id is not None:
            existing = store.cognitive_record(
                agent_id,
                f"place-state:{signature}",
            )
            payload = dict(existing["payload"]) if existing else {}
            payload["visit_count"] = int(payload.get("visit_count", 0)) + 1
            payload["last_seen_sequence"] = frame.sequence
            payload["known_dead_end"] = bool(payload.get("known_dead_end", False))
            payload["relative_pose"] = {
                "x": round(self.pose_x, 4),
                "z": round(self.pose_z, 4),
                "heading_rad": round(self.heading_rad, 4),
                "uncertainty": round(self.pose_uncertainty, 4),
            }
            store.upsert_cognitive_record(
                agent_id=agent_id,
                record_key=f"place-state:{signature}",
                record_kind="spatial_place",
                payload=payload,
                sequence=frame.sequence,
                confidence=min(0.98, 0.45 + 0.04 * payload["visit_count"]),
            )
        return signature

    def begin_action(self, action: dict[str, Any]) -> None:
        self._pending_action = action
        self._pending_origin = self.current_place
        self._pending_heading = self.heading_rad

    def finish_action(
        self,
        action: dict[str, Any],
        supported: bool,
        quality: float,
        frame: PerceptionFrame,
        *,
        store: Store | None = None,
        agent_id: str | None = None,
        goal_kind: str | None = None,
    ) -> None:
        parameters = action.get("parameters")
        parameters = parameters if isinstance(parameters, dict) else {}
        destination = perceptual_place_signature(frame)

        if action.get("type") == "look" and supported:
            yaw = parameters.get("yaw_delta_rad")
            if isinstance(yaw, (int, float)) and not isinstance(yaw, bool):
                self.heading_rad = _normalize_angle(
                    self.heading_rad + float(yaw)
                )

        if action.get("type") == "move":
            origin = self._pending_origin
            maneuver = LocalNavigator.maneuver_from_parameters(parameters)
            returning = goal_kind == "spatial_backtrack" and self._backtracking and bool(self._route)
            if returning:
                # A motor success is NOT proof that the previous perceptual
                # place was reached. Backtracking may span several steps.
                self._backtrack_attempts += 1
            if origin is not None and supported and quality >= 0.55:
                self._failed_moves[origin] = max(
                    0,
                    self._failed_moves.get(origin, 0) - 1,
                )
                forward = parameters.get("forward", 0.0)
                strafe = parameters.get("strafe", 0.0)
                forward = float(forward) if isinstance(forward, (int, float)) and not isinstance(forward, bool) else 0.0
                strafe = float(strafe) if isinstance(strafe, (int, float)) and not isinstance(strafe, bool) else 0.0
                norm = math.hypot(forward, strafe)
                if norm > 1e-6:
                    forward /= norm
                    strafe /= norm
                    # Internal coordinates are relative only: heading=0 means +Z,
                    # positive strafe means body-right.
                    right_x = math.cos(self._pending_heading)
                    right_z = math.sin(self._pending_heading)
                    forward_x = -math.sin(self._pending_heading)
                    forward_z = math.cos(self._pending_heading)
                    distance = max(0.05, min(1.5, float(quality)))
                    self.pose_x += (forward * forward_x + strafe * right_x) * distance
                    self.pose_z += (forward * forward_z + strafe * right_z) * distance
                    self.pose_uncertainty = min(
                        1.0,
                        self.pose_uncertainty + 0.015 + 0.04 * (1.0 - quality),
                    )
                if returning:
                    # Never turn an unfinished return step into a new outward
                    # route: that creates A->B->A ping-pong on aliased views.
                    if self._route and destination == self._route[-1].origin:
                        self._route.pop()
                        self._backtracking = False
                        self._backtrack_attempts = 0
                        self.pose_uncertainty = max(0.04, self.pose_uncertainty * 0.72)
                elif destination != origin:
                    if (
                        self._route
                        and self._route[-1].origin == destination
                        and self._route[-1].destination == origin
                    ):
                        self._route.pop()
                        self._backtracking = False
                        self._backtrack_attempts = 0
                        # Recognizing a previously visited perceptual place is
                        # a weak loop-closure event and reduces odometry drift.
                        self.pose_uncertainty = max(0.04, self.pose_uncertainty * 0.72)
                    else:
                        self._route.append(
                            RouteStep(
                                origin=origin,
                                destination=destination,
                                departure_heading=self._pending_heading,
                                maneuver=maneuver,
                                inverse_maneuver=_inverse_maneuver(maneuver),
                                sequence=frame.sequence,
                            )
                        )
                        if len(self._route) > self.route_capacity:
                            self._route = self._route[-self.route_capacity :]
            elif origin is not None:
                self._failed_moves[origin] = min(
                    12,
                    self._failed_moves.get(origin, 0) + 1,
                )

            if store is not None and agent_id is not None and origin is not None:
                key = f"route:{origin}:{maneuver}:{destination}"
                record = store.cognitive_record(agent_id, key)
                payload = dict(record["payload"]) if record else {
                    "origin": origin,
                    "destination": destination,
                    "maneuver": maneuver,
                    "successes": 0,
                    "failures": 0,
                }
                if supported and quality >= 0.55:
                    payload["successes"] = int(payload.get("successes", 0)) + 1
                else:
                    payload["failures"] = int(payload.get("failures", 0)) + 1
                payload["mean_progress"] = round(
                    (
                        float(payload.get("mean_progress", quality))
                        * max(0, int(payload["successes"]) + int(payload["failures"]) - 1)
                        + quality
                    )
                    / max(1, int(payload["successes"]) + int(payload["failures"])),
                    6,
                )
                store.upsert_cognitive_record(
                    agent_id=agent_id,
                    record_key=key,
                    record_kind="spatial_transition",
                    payload=payload,
                    sequence=frame.sequence,
                    supported=supported and quality >= 0.55,
                )

        self.current_place = destination
        self._pending_action = None
        self._pending_origin = None

    @staticmethod
    def _dead_end_from_model(model: EgocentricWorldModel) -> bool:
        # A blocked *vision* ray is not a dead end if the body's fresh
        # locomotion sense confirms this is a vaultable one-node step.
        if model.front_step_traversable():
            return False
        front = model.sectors["front"]
        left = model.sectors["left"]
        right = model.sectors["right"]
        closed = 0
        for sector in (front, left, right):
            if (
                sector.confidence >= 0.18
                and (
                    sector.blocked_probability >= 0.55
                    or sector.openness <= 0.14
                )
            ):
                closed += 1
        return closed >= 3

    def dead_end_score(
        self,
        model: EgocentricWorldModel,
        revisit_ratio: float,
    ) -> float:
        place = self.current_place
        failed = self._failed_moves.get(place or "", 0)
        score = 0.0
        if self._dead_end_from_model(model):
            score += 0.62
        score += min(0.28, failed * 0.07)
        score += min(0.20, max(0.0, revisit_ratio) * 0.20)
        if not self._route:
            score *= 0.45
        return min(1.0, score)

    def backtrack_directive(
        self,
        model: EgocentricWorldModel,
        *,
        revisit_ratio: float = 0.0,
        force: bool = False,
    ) -> SpatialDirective | None:
        if not self._route or self.current_place is None:
            self._backtracking = False
            self._backtrack_attempts = 0
            return None
        step = self._route[-1]
        if step.destination != self.current_place and not self._backtracking:
            return None
        if self._backtracking and self._backtrack_attempts >= self._backtrack_attempt_limit:
            # Eight verified attempts without recognizing the remembered
            # predecessor invalidate this route edge, NOT its World position.
            # Forget unreliable route evidence instead of replaying it forever.
            self._route.pop()
            self._backtracking = False
            self._backtrack_attempts = 0
            return None

        score = self.dead_end_score(model, revisit_ratio)
        if not force and score < 0.62 and not self._backtracking:
            return None

        heading_error = _normalize_angle(
            step.departure_heading - self.heading_rad
        )
        if abs(heading_error) > 0.22:
            self._backtracking = True
            return SpatialDirective(
                kind="turn",
                reason="return_to_known_route",
                yaw_delta_rad=max(-0.85, min(0.85, heading_error)),
                target_place=step.origin,
                confidence=max(0.60, score),
            )

        self._backtracking = True
        return SpatialDirective(
            kind="move",
            reason="backtrack_to_previous_place",
            maneuver=step.inverse_maneuver,
            target_place=step.origin,
            confidence=max(0.65, score),
        )

    def mark_current_dead_end(
        self,
        store: Store,
        agent_id: str,
        sequence: int,
    ) -> None:
        if self.current_place is None:
            return
        key = f"place-state:{self.current_place}"
        existing = store.cognitive_record(agent_id, key)
        payload = dict(existing["payload"]) if existing else {}
        payload["known_dead_end"] = True
        payload["dead_end_confirmations"] = (
            int(payload.get("dead_end_confirmations", 0)) + 1
        )
        payload["last_dead_end_sequence"] = int(sequence)
        store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=key,
            record_kind="spatial_place",
            payload=payload,
            sequence=sequence,
            supported=True,
        )

    def diagnostics(self) -> dict[str, Any]:
        return {
            "current_place": self.current_place,
            "heading_rad": round(self.heading_rad, 4),
            "relative_pose": {
                "x": round(self.pose_x, 4),
                "z": round(self.pose_z, 4),
                "uncertainty": round(self.pose_uncertainty, 4),
            },
            "route_depth": len(self._route),
            "backtracking": self._backtracking,
            "backtrack_attempts": self._backtrack_attempts,
            "failed_moves_here": self._failed_moves.get(
                self.current_place or "",
                0,
            ),
            "visit_count_here": self._visits.get(
                self.current_place or "",
                0,
            ),
            "return_target": (
                self._route[-1].origin
                if self._route and self._route[-1].destination == self.current_place
                else None
            ),
        }
