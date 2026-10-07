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
    def _nearest_target(
        frame: PerceptionFrame,
        *,
        require_target_ref: bool = False,
    ) -> TargetPercept | None:
        candidates = [
            target
            for target in frame.targets
            if target.distance_fraction is not None
            and (not require_target_ref or target.target_ref is not None)
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda item: (
                item.distance_fraction if item.distance_fraction is not None else 1.0,
                item.ray_index,
            ),
        )

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
        nearest = self._nearest_target(frame, require_target_ref=True)
        explore_stats = goal_stats("explore:open")

        if (
            nearest
            and nearest.appearance_id
            and nearest.distance_fraction is not None
            and nearest.distance_fraction <= 0.08
        ):
            key = f"inspect:{nearest.appearance_id}"
            inspect_stats = goal_stats(key)
            attempts = int(inspect_stats.get("attempts", 0)) if inspect_stats else 0
            failures = int(inspect_stats.get("failures", 0)) if inspect_stats else 0
            novel = nearest.appearance_id in novel_appearance_ids
            needs_verification = attempts < 3 and failures < 2
            if novel or needs_verification:
                # Ověření známého, ale ještě nejistého objektu musí mít dočasně
                # vyšší informační prioritu než obecný scan překážky. Po třetím
                # pokusu kandidát inspect_object zanikne přes needs_verification.
                base = 0.95 if novel else max(0.80, 0.86 - attempts * 0.03)
                candidates.append(
                    GoalCandidate(
                        key=key,
                        kind="inspect_object",
                        priority=self._adjust_priority(base, inspect_stats),
                        target_ref=nearest.target_ref,
                        target_signature=nearest.appearance_id,
                        reason={
                            "selector": "intrinsic_curriculum",
                            "novelty": 1.0 if novel else 0.0,
                            "verification_attempt": attempts + 1,
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
            scan_stats = goal_stats(key)
            last_scan = int(scan_stats.get("last_sequence", -1)) if scan_stats else -1
            last_explore = int(explore_stats.get("last_sequence", -1)) if explore_stats else -1
            # Jedno rozhlédnutí musí být následováno pokusem o pohyb. Bez této
            # brány mohl úspěšný look zůstat nejvyšší prioritou donekonečna.
            needs_scan = scan_stats is None or last_explore > last_scan
            if needs_scan:
                attempts = int(scan_stats.get("attempts", 0)) if scan_stats else 0
                candidates.append(
                    GoalCandidate(
                        key=key,
                        kind="scan_obstacle",
                        priority=self._adjust_priority(0.78, scan_stats),
                        reason={
                            "selector": "intrinsic_curriculum",
                            "distance_fraction": central.distance_fraction,
                            "scan_attempt": attempts + 1,
                            "after_explore_sequence": last_explore,
                        },
                    )
                )

        if explore_stats and int(explore_stats.get("failures", 0)) >= 2:
            key = "scan:recovery"
            recovery_stats = goal_stats(key)
            last_recovery = int(recovery_stats.get("last_sequence", -1)) if recovery_stats else -1
            last_explore = int(explore_stats.get("last_sequence", -1))
            # Recovery scan je reakce na NOVÝ neúspěšný pokus o exploration.
            # Po jednom scanu musí agent zkusit jinou motorickou akci, jinak
            # vzniká nekonečný look loop.
            if recovery_stats is None or last_explore > last_recovery:
                attempts = int(recovery_stats.get("attempts", 0)) if recovery_stats else 0
                candidates.append(
                    GoalCandidate(
                        key=key,
                        kind="scan_recovery",
                        priority=self._adjust_priority(0.84, recovery_stats),
                        reason={
                            "selector": "intrinsic_curriculum",
                            "trigger": "repeated_exploration_failure",
                            "explore_failures": int(explore_stats.get("failures", 0)),
                            "scan_attempt": attempts + 1,
                            "after_explore_sequence": last_explore,
                        },
                    )
                )

        if frame.sequence % 5 == 0:
            key = "scan:periodic"
            periodic_stats = goal_stats(key)
            attempts = int(periodic_stats.get("attempts", 0)) if periodic_stats else 0
            candidates.append(
                GoalCandidate(
                    key=key,
                    kind="scan_periodic",
                    priority=self._adjust_priority(0.56, periodic_stats),
                    reason={
                        "selector": "intrinsic_curriculum",
                        "trigger": "periodic_information_gain",
                        "scan_attempt": attempts + 1,
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
                    "explore_attempt": int(explore_stats.get("attempts", 0)) + 1
                    if explore_stats
                    else 1,
                },
            )
        )

        return max(candidates, key=lambda item: (item.priority, item.key))
