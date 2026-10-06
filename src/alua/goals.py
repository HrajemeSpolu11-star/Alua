from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .memory import WorkingMemory
from .perception import PerceptionFrame, TargetPercept


@dataclass(frozen=True, slots=True)
class GoalCandidate:
    key: str
    kind: str
    priority: float
    target_ref: str | None = None
    target_signature: str | None = None
    reason: dict[str, Any] | None = None


class ReflexGoalSelector:
    """Immediate deterministic body-preservation goal selector."""

    def choose(self, frame: PerceptionFrame, memory: WorkingMemory) -> GoalCandidate | None:
        damage = memory.recent_damage_signal()
        if damage <= 0.02:
            return None
        return GoalCandidate(
            key="survive:damage",
            kind="survive_damage",
            priority=1.0,
            reason={
                "selector": "reflex",
                "observation_sequence": frame.sequence,
                "damage_signal": damage,
            },
        )


class IntrinsicCurriculum:
    """Evidence-driven curriculum built only from Alua's own percepts/history."""

    @staticmethod
    def _nearest_target(frame: PerceptionFrame) -> TargetPercept | None:
        candidates = [target for target in frame.targets if target.distance_fraction is not None]
        if not candidates:
            return None
        return min(candidates, key=lambda item: (item.distance_fraction or 1.0, item.ray_index))

    @staticmethod
    def _adjust_priority(base: float, stats: dict[str, Any] | None) -> float:
        if not stats:
            return base
        failures = int(stats.get("failures", 0))
        successes = int(stats.get("successes", 0))
        attempts = int(stats.get("attempts", 0))
        unresolved = max(0, attempts - successes - failures)
        penalty = min(0.55, failures * 0.12 + unresolved * 0.02)
        return max(0.05, base - penalty)

    def choose(
        self,
        frame: PerceptionFrame,
        novel_appearance_ids: set[str],
        memory: WorkingMemory,
        goal_stats: Callable[[str], dict[str, Any] | None],
    ) -> GoalCandidate:
        candidates: list[GoalCandidate] = []
        nearest = self._nearest_target(frame)

        if (
            nearest
            and nearest.appearance_id
            and nearest.appearance_id in novel_appearance_ids
            and nearest.distance_fraction is not None
            and nearest.distance_fraction <= 0.08
        ):
            key = f"inspect:{nearest.appearance_id}"
            candidates.append(
                GoalCandidate(
                    key=key,
                    kind="inspect_novel",
                    priority=self._adjust_priority(0.95, goal_stats(key)),
                    target_ref=nearest.target_ref,
                    target_signature=nearest.appearance_id,
                    reason={
                        "selector": "intrinsic_curriculum",
                        "novelty": 1.0,
                        "distance_fraction": nearest.distance_fraction,
                        "ray_index": nearest.ray_index,
                    },
                )
            )

        central = next((target for target in frame.targets if target.ray_index == 0), None)
        if (
            central
            and central.blocks_motion
            and central.distance_fraction is not None
            and central.distance_fraction < 0.12
        ):
            key = "scan:obstacle"
            candidates.append(
                GoalCandidate(
                    key=key,
                    kind="scan_obstacle",
                    priority=self._adjust_priority(0.78, goal_stats(key)),
                    reason={
                        "selector": "intrinsic_curriculum",
                        "distance_fraction": central.distance_fraction,
                    },
                )
            )

        explore_stats = goal_stats("explore:open")
        if explore_stats and int(explore_stats.get("failures", 0)) >= 2:
            key = "scan:recovery"
            candidates.append(
                GoalCandidate(
                    key=key,
                    kind="scan_recovery",
                    priority=self._adjust_priority(0.84, goal_stats(key)),
                    reason={
                        "selector": "intrinsic_curriculum",
                        "trigger": "repeated_exploration_failure",
                        "explore_failures": int(explore_stats.get("failures", 0)),
                    },
                )
            )

        if frame.sequence % 5 == 0:
            key = "scan:periodic"
            candidates.append(
                GoalCandidate(
                    key=key,
                    kind="scan_periodic",
                    priority=self._adjust_priority(0.56, goal_stats(key)),
                    reason={
                        "selector": "intrinsic_curriculum",
                        "trigger": "periodic_information_gain",
                    },
                )
            )

        key = "explore:open"
        candidates.append(
            GoalCandidate(
                key=key,
                kind="explore",
                priority=self._adjust_priority(0.50, explore_stats),
                reason={
                    "selector": "intrinsic_curriculum",
                    "trigger": "default_exploration",
                    "working_memory_frames": len(memory),
                },
            )
        )

        return max(candidates, key=lambda item: (item.priority, item.key))
