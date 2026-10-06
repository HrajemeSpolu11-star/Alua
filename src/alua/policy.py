from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .goals import GoalCandidate
from .memory import WorkingMemory
from .perception import PerceptionFrame


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
            direction = 1 if frame.sequence % 2 == 0 else -1
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
