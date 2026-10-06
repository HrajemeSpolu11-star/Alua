from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .memory import WorkingMemory
from .perception import PerceptionFrame, TargetPercept


@dataclass(frozen=True, slots=True)
class ActionIntent:
    action_type: str
    parameters: dict[str, Any]
    duration: float | None
    target_ref: str | None
    target_signature: str | None
    rationale: dict[str, Any]


class ExplorationPolicy:
    """Small deterministic policy for the first embodied Alua.

    It uses only the motor contract explicitly defined by AluaWorld.
    Destructive manipulation is not selected. The only target interaction
    in this stage is touch at short perceptual distance.
    """

    def _nearest_target(self, frame: PerceptionFrame) -> TargetPercept | None:
        candidates = [
            target for target in frame.targets
            if target.distance_fraction is not None
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda item: (item.distance_fraction or 1.0, item.ray_index))

    def choose(
        self,
        frame: PerceptionFrame,
        novel_appearance_ids: set[str],
        memory: WorkingMemory,
    ) -> ActionIntent:
        if memory.recent_damage_signal() > 0.02:
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
                    "policy": "damage_avoidance",
                    "observation_sequence": frame.sequence,
                    "damage_signal": memory.recent_damage_signal(),
                },
            )

        nearest = self._nearest_target(frame)
        if (
            nearest
            and nearest.appearance_id
            and nearest.appearance_id in novel_appearance_ids
            and nearest.distance_fraction is not None
            and nearest.distance_fraction <= 0.08
        ):
            return ActionIntent(
                action_type="manipulate",
                parameters={"verb": "touch"},
                duration=None,
                target_ref=nearest.target_ref,
                target_signature=nearest.appearance_id,
                rationale={
                    "policy": "safe_touch_novelty",
                    "observation_sequence": frame.sequence,
                    "appearance_id": nearest.appearance_id,
                    "distance_fraction": nearest.distance_fraction,
                },
            )

        central = next((target for target in frame.targets if target.ray_index == 0), None)
        if central and central.blocks_motion and central.distance_fraction is not None and central.distance_fraction < 0.12:
            direction = 1 if frame.sequence % 2 == 0 else -1
            return ActionIntent(
                action_type="look",
                parameters={"yaw_delta_rad": 0.45 * direction, "pitch_delta_rad": 0.0},
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={
                    "policy": "obstacle_scan",
                    "observation_sequence": frame.sequence,
                    "distance_fraction": central.distance_fraction,
                },
            )

        if frame.sequence % 5 == 0:
            direction = 1 if (frame.sequence // 5) % 2 == 0 else -1
            return ActionIntent(
                action_type="look",
                parameters={"yaw_delta_rad": 0.30 * direction, "pitch_delta_rad": 0.0},
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={
                    "policy": "periodic_scan",
                    "observation_sequence": frame.sequence,
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
                "policy": "cautious_exploration",
                "observation_sequence": frame.sequence,
            },
        )


BootstrapPolicy = ExplorationPolicy
