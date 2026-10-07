from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from .embodiment import inventory_load, inventory_slots, locomotion_signals, vital_signals
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
        vitals = vital_signals(frame)
        locomotion = locomotion_signals(frame)
        if (
            float(locomotion.get("head_submerged_signal", 0.0)) >= 0.5
            and vitals.breath <= 0.30
        ):
            return GoalCandidate(
                key="survive:breath",
                kind="survive_breath",
                priority=1.25,
                reason={
                    "selector": "reflex",
                    "observation_sequence": frame.sequence,
                    "breath_fraction": vitals.breath,
                },
            )

        damage = memory.recent_damage_signal()
        if damage > 0.02:
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
        return None


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
        previous_goal_kind: str | None = None,
        previous_action_type: str | None = None,
        information_need: float | None = None,
        candidate_ranker: Callable[[GoalCandidate], float] | None = None,
        belief_lookup: Callable[[str], dict[str, Any] | None] | None = None,
    ) -> GoalCandidate:
        candidates: list[GoalCandidate] = []
        nearest = self._nearest_target(frame, require_target_ref=True)
        explore_stats = goal_stats("explore:open")
        vitals = vital_signals(frame)
        locomotion = locomotion_signals(frame)
        slots = inventory_slots(frame)

        def belief_supports(key: str) -> bool:
            if belief_lookup is None:
                return False
            belief = belief_lookup(key)
            if not belief:
                return False
            return int(belief.get("support_count", 0)) > int(belief.get("contradiction_count", 0))

        if vitals.stamina <= 0.28 or vitals.fatigue >= 0.74:
            key = "need:recover"
            candidates.append(
                GoalCandidate(
                    key=key,
                    kind="recover_stamina",
                    priority=max(0.72, 0.92 - vitals.stamina * 0.45 + vitals.fatigue * 0.12),
                    reason={
                        "selector": "body_need",
                        "stamina_fraction": vitals.stamina,
                        "fatigue_signal": vitals.fatigue,
                    },
                )
            )

        if vitals.thirst >= 0.34:
            liquid_targets = [
                target
                for target in frame.targets
                if target.target_ref
                and target.liquid is True
                and target.distance_fraction is not None
            ]
            liquid_targets.sort(key=lambda target: (target.distance_fraction, target.ray_index))
            viable_liquid = None
            for item in liquid_targets:
                if item.appearance_id and belief_lookup is not None:
                    hydration_belief = belief_lookup(
                        f"appearance:{item.appearance_id}:drink:hydration_effect"
                    )
                    if (
                        hydration_belief
                        and int(hydration_belief.get("contradiction_count", 0))
                        > int(hydration_belief.get("support_count", 0))
                    ):
                        continue
                attempts = (
                    goal_stats(f"need:drink:{item.appearance_id}")
                    if item.appearance_id
                    else None
                )
                failures = int(attempts.get("failures", 0)) if attempts else 0
                if failures < 2 or (
                    item.appearance_id
                    and belief_supports(
                        f"appearance:{item.appearance_id}:drink:hydration_effect"
                    )
                ):
                    viable_liquid = item
                    break

            phase = "search"
            if viable_liquid is not None:
                phase = (
                    "drink"
                    if viable_liquid.distance_fraction is not None
                    and viable_liquid.distance_fraction <= 0.11
                    else "approach"
                )
            candidates.append(
                GoalCandidate(
                    key=(
                        f"need:drink:{viable_liquid.appearance_id}"
                        if viable_liquid and viable_liquid.appearance_id
                        else "need:thirst:search"
                    ),
                    kind="satisfy_thirst",
                    priority=min(1.08, 0.68 + 0.40 * vitals.thirst),
                    target_ref=viable_liquid.target_ref if viable_liquid else None,
                    target_signature=viable_liquid.appearance_id if viable_liquid else None,
                    reason={
                        "selector": "body_need",
                        "thirst_signal": vitals.thirst,
                        "phase": phase,
                    },
                )
            )

        if vitals.hunger >= 0.34:
            selected_slot = None
            unknown_slot = None
            for slot in slots:
                if belief_supports(
                    f"appearance:{slot.appearance_id}:consume:nutrition_effect"
                ):
                    selected_slot = slot
                    break
                stats = goal_stats(f"need:consume:{slot.appearance_id}")
                failures = int(stats.get("failures", 0)) if stats else 0
                if unknown_slot is None and failures < 2:
                    unknown_slot = slot
            selected_slot = selected_slot or unknown_slot

            visible_known_food = next(
                (
                    target for target in frame.targets
                    if target.target_ref
                    and target.appearance_id
                    and target.distance_fraction is not None
                    and belief_supports(
                        f"appearance:{target.appearance_id}:consume:nutrition_effect"
                    )
                ),
                None,
            )

            if selected_slot is not None:
                candidates.append(
                    GoalCandidate(
                        key=f"need:consume:{selected_slot.appearance_id}",
                        kind="satisfy_hunger",
                        priority=min(1.04, 0.66 + 0.38 * vitals.hunger),
                        target_signature=selected_slot.appearance_id,
                        reason={
                            "selector": "body_need",
                            "hunger_signal": vitals.hunger,
                            "phase": "consume_inventory",
                            "slot_index": selected_slot.slot_index,
                        },
                    )
                )
            elif visible_known_food is not None:
                distance = visible_known_food.distance_fraction or 1.0
                pickup_stats = goal_stats(f"need:pickup:{visible_known_food.appearance_id}")
                pickup_failures = int(pickup_stats.get("failures", 0)) if pickup_stats else 0
                mine = distance <= 0.11 and pickup_failures >= 2
                phase = (
                    "approach"
                    if distance > 0.11
                    else ("mine_required" if mine else "pickup_required")
                )
                candidates.append(
                    GoalCandidate(
                        key=(
                            f"need:mine:{visible_known_food.appearance_id}"
                            if mine
                            else f"need:pickup:{visible_known_food.appearance_id}"
                        ),
                        kind="acquire_required_resource" if mine else "satisfy_hunger",
                        priority=min(1.02, 0.67 + 0.36 * vitals.hunger),
                        target_ref=visible_known_food.target_ref,
                        target_signature=visible_known_food.appearance_id,
                        reason={
                            "selector": "body_need",
                            "hunger_signal": vitals.hunger,
                            "phase": phase,
                        },
                    )
                )
            else:
                candidates.append(
                    GoalCandidate(
                        key="need:hunger:search",
                        kind="satisfy_hunger",
                        priority=min(0.98, 0.62 + 0.34 * vitals.hunger),
                        reason={
                            "selector": "body_need",
                            "hunger_signal": vitals.hunger,
                            "phase": "search",
                        },
                    )
                )

        if (
            nearest
            and nearest.appearance_id
            and nearest.target_ref
            and nearest.distance_fraction is not None
            and nearest.distance_fraction <= 0.08
            and inventory_load(frame) < 0.85
        ):
            inspect_stats = goal_stats(f"inspect:{nearest.appearance_id}")
            collect_stats = goal_stats(f"collect:{nearest.appearance_id}")
            inspected = int(inspect_stats.get("attempts", 0)) if inspect_stats else 0
            collected_attempts = int(collect_stats.get("attempts", 0)) if collect_stats else 0
            if inspected >= 1 and collected_attempts < 2:
                candidates.append(
                    GoalCandidate(
                        key=f"collect:{nearest.appearance_id}",
                        kind="collect_object",
                        priority=0.88 if nearest.appearance_id in novel_appearance_ids else 0.76,
                        target_ref=nearest.target_ref,
                        target_signature=nearest.appearance_id,
                        reason={
                            "selector": "intrinsic_curriculum",
                            "trigger": "inspect_then_collect",
                            "inventory_load": inventory_load(frame),
                        },
                    )
                )
        scan_kinds = {"scan_obstacle", "scan_recovery", "scan_periodic"}
        scan_allowed = (
            previous_goal_kind not in scan_kinds
            and previous_action_type != "look"
        )

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
            scan_allowed
            and central
            and central.blocks_motion
            and central.distance_fraction is not None
            and central.distance_fraction < 0.12
        ):
            key = "scan:obstacle"
            scan_stats = goal_stats(key)
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
                        "global_scan_gate": "open",
                    },
                )
            )

        explore_failures = int(explore_stats.get("failures", 0)) if explore_stats else 0
        explore_successes = int(explore_stats.get("successes", 0)) if explore_stats else 0
        if (
            scan_allowed
            and explore_stats
            and explore_failures >= 2
            and explore_failures > explore_successes
        ):
            key = "scan:recovery"
            recovery_stats = goal_stats(key)
            attempts = int(recovery_stats.get("attempts", 0)) if recovery_stats else 0
            candidates.append(
                GoalCandidate(
                    key=key,
                    kind="scan_recovery",
                    priority=self._adjust_priority(0.84, recovery_stats),
                    reason={
                        "selector": "intrinsic_curriculum",
                        "trigger": "repeated_exploration_failure",
                        "explore_failures": explore_failures,
                        "explore_successes": explore_successes,
                        "scan_attempt": attempts + 1,
                        "global_scan_gate": "open",
                    },
                )
            )

        if information_need is None:
            should_information_scan = frame.sequence % 5 == 0
            information_need_value = 0.50 if should_information_scan else 0.0
            scan_trigger = "legacy_periodic_information_gain"
        else:
            information_need_value = max(0.0, min(1.0, float(information_need)))
            should_information_scan = information_need_value >= 0.58
            scan_trigger = "model_uncertainty"

        if scan_allowed and should_information_scan:
            key = "scan:periodic"
            periodic_stats = goal_stats(key)
            attempts = int(periodic_stats.get("attempts", 0)) if periodic_stats else 0
            base_priority = 0.54 + 0.10 * information_need_value
            candidates.append(
                GoalCandidate(
                    key=key,
                    kind="scan_periodic",
                    priority=self._adjust_priority(base_priority, periodic_stats),
                    reason={
                        "selector": "intrinsic_curriculum",
                        "trigger": scan_trigger,
                        "information_need": information_need_value,
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

        if candidate_ranker is None:
            return max(candidates, key=lambda item: (item.priority, item.key))

        scored = [(float(candidate_ranker(item)), item) for item in candidates]
        score, selected = max(scored, key=lambda pair: (pair[0], pair[1].priority, pair[1].key))
        reason = dict(selected.reason or {})
        reason["adaptive_utility_score"] = round(score, 6)
        return GoalCandidate(
            key=selected.key,
            kind=selected.kind,
            priority=selected.priority,
            target_ref=selected.target_ref,
            target_signature=selected.target_signature,
            reason=reason,
        )
