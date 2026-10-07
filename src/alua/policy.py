from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .goals import GoalCandidate
from .memory import WorkingMemory
from .perception import PerceptionFrame


def available_effector(frame: PerceptionFrame, capability: str) -> str | None:
    """Return a currently usable named hand for a capability from body_schema."""
    def signal(value: Any) -> float:
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return float(value)
        return 0.0

    channels = frame.persistent.get("channels")
    if not isinstance(channels, dict):
        return None
    body_schema = channels.get("body_schema")
    if not isinstance(body_schema, dict):
        return None
    effectors = body_schema.get("effectors")
    if not isinstance(effectors, dict):
        return None
    signal_name = capability + "_signal"
    for name in ("hand_right", "hand_left"):
        state = effectors.get(name)
        if not isinstance(state, dict):
            continue
        if signal(state.get("present_signal")) < 0.5:
            continue
        if signal(state.get(signal_name)) < 0.5:
            continue
        if signal(state.get("occupied_signal")) >= 0.5:
            continue
        return name
    return None


def near_central_obstacle(frame: PerceptionFrame, threshold: float = 0.15) -> bool:
    central = next((target for target in frame.targets if target.ray_index == 0), None)
    return bool(
        central
        and central.blocks_motion
        and central.distance_fraction is not None
        and central.distance_fraction < threshold
    )


@dataclass(frozen=True, slots=True)
class ActionIntent:
    action_type: str
    parameters: dict[str, Any]
    duration: float | None
    target_ref: str | None
    target_signature: str | None
    rationale: dict[str, Any]


class ExplorationPolicy:
    """Maps an already selected safe goal to one primitive World action."""

    @staticmethod
    def _available_hand(frame: PerceptionFrame, capability: str) -> str | None:
        return available_effector(frame, capability)

    def choose(
        self,
        frame: PerceptionFrame,
        goal: GoalCandidate,
        memory: WorkingMemory,
    ) -> ActionIntent:
        common = {
            "goal_key": goal.key,
            "goal_kind": goal.kind,
            "goal_priority": goal.priority,
            "observation_sequence": frame.sequence,
        }

        if goal.kind == "survive_damage":
            return ActionIntent(
                action_type="move",
                parameters={
                    "forward": -1.0,
                    "strafe": 0.0,
                    "duration_s": 0.35,
                    "speed_fraction": 0.75,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={
                    **common,
                    "policy": "reflex_damage_avoidance",
                    "damage_signal": memory.recent_damage_signal(),
                },
            )

        if goal.kind == "inspect_object" and goal.target_ref:
            effector = self._available_hand(frame, "touch")
            parameters = {"verb": "touch"}
            if effector:
                parameters["effector"] = effector
            return ActionIntent(
                action_type="manipulate",
                parameters=parameters,
                duration=None,
                target_ref=goal.target_ref,
                target_signature=goal.target_signature,
                rationale={
                    **common,
                    "policy": "safe_touch_novelty",
                    "appearance_id": goal.target_signature,
                    "effector": effector,
                },
            )

        if goal.kind in {"scan_obstacle", "scan_recovery", "scan_periodic"}:
            reason = goal.reason if isinstance(goal.reason, dict) else {}
            scan_attempt = reason.get("scan_attempt", 1)
            if not isinstance(scan_attempt, int) or isinstance(scan_attempt, bool) or scan_attempt < 1:
                scan_attempt = 1
            # Směr se odvozuje od pořadí skutečných scan pokusů, ne z parity
            # observation sequence. Parita mohla při pravidelném toku vytvořit
            # přesný levá/pravá oscilátor bez nového informačního zisku.
            direction = 1 if ((scan_attempt - 1) // 2) % 2 == 0 else -1
            magnitude = 0.45 if goal.kind != "scan_periodic" else 0.30
            return ActionIntent(
                action_type="look",
                parameters={"yaw_delta_rad": magnitude * direction, "pitch_delta_rad": 0.0},
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={
                    **common,
                    "policy": goal.kind,
                },
            )

        if near_central_obstacle(frame):
            reason = goal.reason if isinstance(goal.reason, dict) else {}
            attempt = reason.get("explore_attempt", 1)
            if not isinstance(attempt, int) or isinstance(attempt, bool) or attempt < 1:
                attempt = 1
            # Po rozhlédnutí nezkoušet znovu slepě stejný krok vpřed.
            # Dva pokusy drží stejnou stranu, pak se směr změní.
            strafe_direction = 1.0 if ((attempt - 1) // 2) % 2 == 0 else -1.0
            return ActionIntent(
                action_type="move",
                parameters={
                    "forward": 0.10,
                    "strafe": 0.70 * strafe_direction,
                    "duration_s": 0.35,
                    "speed_fraction": 0.45,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={
                    **common,
                    "policy": "cautious_obstacle_bypass",
                    "strafe_direction": strafe_direction,
                },
            )

        return ActionIntent(
            action_type="move",
            parameters={
                "forward": 1.0,
                "strafe": 0.0,
                "duration_s": 0.30,
                "speed_fraction": 0.55,
            },
            duration=None,
            target_ref=None,
            target_signature=None,
            rationale={
                **common,
                "policy": "cautious_exploration",
            },
        )


BootstrapPolicy = ExplorationPolicy
