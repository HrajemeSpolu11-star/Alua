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
            return ActionIntent(
                action_type="manipulate",
                parameters={"verb": "touch"},
                duration=None,
                target_ref=goal.target_ref,
                target_signature=goal.target_signature,
                rationale={
                    **common,
                    "policy": "safe_touch_novelty",
                    "appearance_id": goal.target_signature,
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
