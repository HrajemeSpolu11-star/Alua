from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .embodiment import locomotion_signals, vital_signals
from .goals import GoalCandidate
from .memory import WorkingMemory
from .perception import PerceptionFrame, TargetPercept


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
    """Maps selected goals to physical actions without hidden world semantics."""

    @staticmethod
    def _available_hand(frame: PerceptionFrame, capability: str) -> str | None:
        return available_effector(frame, capability)

    @staticmethod
    def _reason(goal: GoalCandidate) -> dict[str, Any]:
        return goal.reason if isinstance(goal.reason, dict) else {}

    @staticmethod
    def _target(frame: PerceptionFrame, goal: GoalCandidate) -> TargetPercept | None:
        for target in frame.targets:
            if goal.target_ref and target.target_ref == goal.target_ref:
                return target
            if (
                goal.target_signature
                and target.appearance_id == goal.target_signature
            ):
                return target
        return None

    @staticmethod
    def _common(frame: PerceptionFrame, goal: GoalCandidate) -> dict[str, Any]:
        return {
            "goal_key": goal.key,
            "goal_kind": goal.kind,
            "goal_priority": goal.priority,
            "observation_sequence": frame.sequence,
        }

    def _approach_target(
        self,
        frame: PerceptionFrame,
        goal: GoalCandidate,
    ) -> ActionIntent | None:
        target = self._target(frame, goal)
        if target is None:
            return None
        common = self._common(frame, goal)
        if target.ray_index == 1:
            return ActionIntent(
                action_type="look",
                parameters={"yaw_delta_rad": 0.34, "pitch_delta_rad": 0.0},
                duration=None,
                target_ref=None,
                target_signature=goal.target_signature,
                rationale={**common, "policy": "approach_visible_target", "turn": "left"},
            )
        if target.ray_index == 2:
            return ActionIntent(
                action_type="look",
                parameters={"yaw_delta_rad": -0.34, "pitch_delta_rad": 0.0},
                duration=None,
                target_ref=None,
                target_signature=goal.target_signature,
                rationale={**common, "policy": "approach_visible_target", "turn": "right"},
            )
        if target.ray_index == 3:
            return ActionIntent(
                action_type="look",
                parameters={"yaw_delta_rad": 0.0, "pitch_delta_rad": -0.16},
                duration=None,
                target_ref=None,
                target_signature=goal.target_signature,
                rationale={**common, "policy": "approach_visible_target", "turn": "down"},
            )
        if target.ray_index == 4:
            return ActionIntent(
                action_type="look",
                parameters={"yaw_delta_rad": 0.0, "pitch_delta_rad": 0.16},
                duration=None,
                target_ref=None,
                target_signature=goal.target_signature,
                rationale={**common, "policy": "approach_visible_target", "turn": "up"},
            )
        return ActionIntent(
            action_type="move",
            parameters={
                "mode": "walk",
                "forward": 1.0,
                "strafe": 0.0,
                "duration_s": 0.30,
                "speed_fraction": 0.45,
            },
            duration=None,
            target_ref=None,
            target_signature=goal.target_signature,
            rationale={**common, "policy": "approach_visible_target", "turn": "none"},
        )

    def terrain_intent(
        self,
        frame: PerceptionFrame,
        goal: GoalCandidate,
        memory: WorkingMemory,
    ) -> ActionIntent | None:
        """Choose a special locomotion primitive only from current bodily affordances."""
        signals = locomotion_signals(frame)
        if not signals:
            return None
        vitals = vital_signals(frame)
        common = self._common(frame, goal)

        head_submerged = float(signals.get("head_submerged_signal", 0.0)) >= 0.5
        feet_in_liquid = float(signals.get("feet_in_liquid_signal", 0.0)) >= 0.5
        if head_submerged or feet_in_liquid:
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "swim",
                    "forward": 0.70,
                    "strafe": 0.0,
                    "vertical": 0.70 if head_submerged else 0.05,
                    "duration_s": 0.40,
                    "speed_fraction": 0.65,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={
                    **common,
                    "policy": "embodied_swim",
                    "head_submerged": head_submerged,
                },
            )

        if (
            float(signals.get("climbable_signal", 0.0)) >= 0.5
            and near_central_obstacle(frame, 0.20)
        ):
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "climb",
                    "forward": 0.15,
                    "strafe": 0.0,
                    "vertical": 1.0,
                    "duration_s": 0.45,
                    "speed_fraction": 0.70,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={**common, "policy": "embodied_climb"},
            )

        if float(signals.get("step_up_signal", 0.0)) >= 0.5:
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "vault",
                    "forward": 1.0,
                    "strafe": 0.0,
                    "vertical": 0.0,
                    "duration_s": 0.65,
                    "speed_fraction": 0.82,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={**common, "policy": "embodied_vault"},
            )

        if (
            float(signals.get("gap_ahead_signal", 0.0)) >= 0.5
            and float(signals.get("jump_gap_signal", 0.0)) >= 0.5
            and vitals.stamina >= 0.22
        ):
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "jump",
                    "forward": 1.0,
                    "strafe": 0.0,
                    "vertical": 0.0,
                    "duration_s": 0.48,
                    "speed_fraction": 0.82,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={**common, "policy": "embodied_gap_jump"},
            )

        if float(signals.get("gap_ahead_signal", 0.0)) >= 0.5:
            if float(signals.get("safe_drop_signal", 0.0)) >= 0.5:
                return ActionIntent(
                    action_type="move",
                    parameters={
                        "mode": "drop",
                        "forward": 0.45,
                        "strafe": 0.0,
                        "vertical": -1.0,
                        "duration_s": 0.35,
                        "speed_fraction": 0.40,
                    },
                    duration=None,
                    target_ref=None,
                    target_signature=None,
                    rationale={**common, "policy": "embodied_safe_drop"},
                )
            strafe = 0.75 if frame.sequence % 2 else -0.75
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "walk",
                    "forward": 0.0,
                    "strafe": strafe,
                    "vertical": 0.0,
                    "duration_s": 0.35,
                    "speed_fraction": 0.42,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={
                    **common,
                    "policy": "avoid_unverified_drop",
                    "strafe": strafe,
                },
            )

        if float(signals.get("crawl_clearance_signal", 0.0)) >= 0.5:
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "crawl",
                    "forward": 0.80,
                    "strafe": 0.0,
                    "vertical": 0.0,
                    "duration_s": 0.45,
                    "speed_fraction": 0.72,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={**common, "policy": "embodied_crawl"},
            )

        if float(signals.get("crouch_clearance_signal", 0.0)) >= 0.5:
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "crouch",
                    "forward": 0.85,
                    "strafe": 0.0,
                    "vertical": 0.0,
                    "duration_s": 0.40,
                    "speed_fraction": 0.72,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={**common, "policy": "embodied_crouch"},
            )

        if (
            not near_central_obstacle(frame)
            and vitals.stamina >= 0.78
            and vitals.fatigue <= 0.45
        ):
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "sprint",
                    "forward": 1.0,
                    "strafe": 0.0,
                    "vertical": 0.0,
                    "duration_s": 0.32,
                    "speed_fraction": 0.68,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={**common, "policy": "embodied_sprint"},
            )

        return None

    def _search_move(
        self,
        frame: PerceptionFrame,
        goal: GoalCandidate,
        memory: WorkingMemory,
    ) -> ActionIntent:
        special = self.terrain_intent(frame, goal, memory)
        if special is not None:
            return special
        common = self._common(frame, goal)
        return ActionIntent(
            action_type="move",
            parameters={
                "mode": "walk",
                "forward": 1.0,
                "strafe": 0.0,
                "vertical": 0.0,
                "duration_s": 0.30,
                "speed_fraction": 0.48,
            },
            duration=None,
            target_ref=None,
            target_signature=None,
            rationale={**common, "policy": "need_search_exploration"},
        )

    def choose(
        self,
        frame: PerceptionFrame,
        goal: GoalCandidate,
        memory: WorkingMemory,
    ) -> ActionIntent:
        common = self._common(frame, goal)
        reason = self._reason(goal)

        if goal.kind == "spatial_backtrack":
            phase = reason.get("phase")
            if phase == "turn":
                yaw = reason.get("yaw_delta_rad")
                yaw = float(yaw) if isinstance(yaw, (int, float)) and not isinstance(yaw, bool) else 0.0
                return ActionIntent(
                    action_type="look",
                    parameters={
                        "yaw_delta_rad": max(-0.85, min(0.85, yaw)),
                        "pitch_delta_rad": 0.0,
                    },
                    duration=None,
                    target_ref=None,
                    target_signature=None,
                    rationale={**common, "policy": "spatial_route_backtrack_turn"},
                )
            maneuver = reason.get("maneuver")
            if maneuver == "forward":
                forward, strafe = 0.72, 0.0
            elif maneuver == "left":
                forward, strafe = 0.10, -0.72
            elif maneuver == "right":
                forward, strafe = 0.10, 0.72
            else:
                forward, strafe = -0.62, 0.0
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "walk",
                    "forward": forward,
                    "strafe": strafe,
                    "vertical": 0.0,
                    "duration_s": 0.34,
                    "speed_fraction": 0.42,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={
                    **common,
                    "policy": "spatial_route_backtrack_move",
                    "maneuver": maneuver,
                    "target_place": reason.get("target_place"),
                },
            )

        if goal.kind == "deliberate_navigation":
            action = reason.get("action")
            if isinstance(action, dict) and action.get("type") == "move":
                parameters = action.get("parameters")
                if isinstance(parameters, dict):
                    return ActionIntent(
                        action_type="move",
                        parameters=dict(parameters),
                        duration=None,
                        target_ref=None,
                        target_signature=None,
                        rationale={
                            **common,
                            "policy": "model_based_counterfactual_navigation",
                            "deliberation": reason.get("deliberation"),
                        },
                    )

        if goal.kind == "survive_breath":
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "swim",
                    "forward": 0.20,
                    "strafe": 0.0,
                    "vertical": 1.0,
                    "duration_s": 0.55,
                    "speed_fraction": 0.90,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={**common, "policy": "reflex_surface_for_breath"},
            )

        if goal.kind == "survive_damage":
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "walk",
                    "forward": -1.0,
                    "strafe": 0.0,
                    "vertical": 0.0,
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

        if goal.kind == "recover_stamina":
            return ActionIntent(
                action_type="interact",
                parameters={"verb": "rest", "posture": "crouch"},
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={**common, "policy": "body_need_rest"},
            )

        if goal.kind == "satisfy_thirst":
            phase = reason.get("phase")
            if phase == "drink" and goal.target_ref:
                return ActionIntent(
                    action_type="manipulate",
                    parameters={"verb": "drink"},
                    duration=None,
                    target_ref=goal.target_ref,
                    target_signature=goal.target_signature,
                    rationale={**common, "policy": "need_drink_experiment"},
                )
            if phase == "approach" and goal.target_ref:
                approach = self._approach_target(frame, goal)
                if approach is not None:
                    return approach
            return self._search_move(frame, goal, memory)

        if goal.kind == "satisfy_hunger":
            phase = reason.get("phase")
            if phase == "consume_inventory":
                slot_index = reason.get("slot_index")
                if isinstance(slot_index, int) and not isinstance(slot_index, bool):
                    return ActionIntent(
                        action_type="interact",
                        parameters={"verb": "consume", "slot_index": slot_index},
                        duration=None,
                        target_ref=None,
                        target_signature=goal.target_signature,
                        rationale={**common, "policy": "need_consume_experiment"},
                    )
            if phase == "pickup_required" and goal.target_ref:
                effector = self._available_hand(frame, "grasp")
                parameters: dict[str, Any] = {"verb": "pickup", "store": True}
                if effector:
                    parameters["effector"] = effector
                return ActionIntent(
                    action_type="manipulate",
                    parameters=parameters,
                    duration=None,
                    target_ref=goal.target_ref,
                    target_signature=goal.target_signature,
                    rationale={**common, "policy": "need_pickup_known_resource"},
                )
            if phase == "approach" and goal.target_ref:
                approach = self._approach_target(frame, goal)
                if approach is not None:
                    return approach
            return self._search_move(frame, goal, memory)

        if goal.kind == "collect_object" and goal.target_ref:
            effector = self._available_hand(frame, "grasp")
            parameters = {"verb": "pickup", "store": True}
            if effector:
                parameters["effector"] = effector
            return ActionIntent(
                action_type="manipulate",
                parameters=parameters,
                duration=None,
                target_ref=goal.target_ref,
                target_signature=goal.target_signature,
                rationale={**common, "policy": "inspect_then_collect"},
            )

        if goal.kind == "acquire_required_resource" and goal.target_ref:
            effector = self._available_hand(frame, "impact")
            parameters = {"verb": "break_object"}
            if effector:
                parameters["effector"] = effector
            return ActionIntent(
                action_type="manipulate",
                parameters=parameters,
                duration=None,
                target_ref=goal.target_ref,
                target_signature=goal.target_signature,
                rationale={**common, "policy": "need_driven_mining"},
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
            scan_attempt = reason.get("scan_attempt", 1)
            if (
                not isinstance(scan_attempt, int)
                or isinstance(scan_attempt, bool)
                or scan_attempt < 1
            ):
                scan_attempt = 1
            direction = 1 if ((scan_attempt - 1) // 2) % 2 == 0 else -1
            magnitude = 0.45 if goal.kind != "scan_periodic" else 0.30
            return ActionIntent(
                action_type="look",
                parameters={
                    "yaw_delta_rad": magnitude * direction,
                    "pitch_delta_rad": 0.0,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={**common, "policy": goal.kind},
            )

        terrain = self.terrain_intent(frame, goal, memory)
        if terrain is not None:
            return terrain

        if near_central_obstacle(frame):
            attempt = reason.get("explore_attempt", 1)
            if (
                not isinstance(attempt, int)
                or isinstance(attempt, bool)
                or attempt < 1
            ):
                attempt = 1
            strafe_direction = 1.0 if ((attempt - 1) // 2) % 2 == 0 else -1.0
            return ActionIntent(
                action_type="move",
                parameters={
                    "mode": "walk",
                    "forward": 0.10,
                    "strafe": 0.70 * strafe_direction,
                    "vertical": 0.0,
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
                "mode": "walk",
                "forward": 1.0,
                "strafe": 0.0,
                "vertical": 0.0,
                "duration_s": 0.30,
                "speed_fraction": 0.55,
            },
            duration=None,
            target_ref=None,
            target_signature=None,
            rationale={**common, "policy": "cautious_exploration"},
        )


BootstrapPolicy = ExplorationPolicy
