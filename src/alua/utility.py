from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .goals import GoalCandidate
from .memory import WorkingMemory


@dataclass(frozen=True, slots=True)
class UtilityBreakdown:
    total: float
    base: float
    empirical_success: float
    information_value: float
    novelty_value: float
    failure_risk: float
    damage_risk: float
    action_cost: float


class AdaptiveUtilityModel:
    """Evidence-weighted goal ranker without hidden world semantics.

    The model does not know what an object *is*. It only combines the intrinsic
    priority with the agent's own success/failure evidence, current uncertainty,
    novelty and recent bodily damage.
    """

    _COSTS = {
        "survive_breath": 0.00,
        "survive_damage": 0.00,
        "recover_stamina": 0.005,
        "satisfy_thirst": 0.02,
        "satisfy_hunger": 0.025,
        "collect_object": 0.05,
        "acquire_required_resource": 0.12,
        "inspect_object": 0.05,
        "scan_obstacle": 0.025,
        "scan_recovery": 0.025,
        "scan_periodic": 0.025,
        "explore": 0.04,
    }

    def evaluate(
        self,
        candidate: GoalCandidate,
        *,
        stats: dict[str, Any] | None,
        memory: WorkingMemory,
        information_need: float,
    ) -> UtilityBreakdown:
        attempts = int(stats.get("attempts", 0)) if stats else 0
        successes = int(stats.get("successes", 0)) if stats else 0
        failures = int(stats.get("failures", 0)) if stats else 0

        # Beta(1,1) prior keeps sparse evidence uncertain instead of absolute.
        empirical_success = (successes + 1) / (successes + failures + 2)
        failure_risk = (failures + 1) / (successes + failures + 2)

        reason = candidate.reason if isinstance(candidate.reason, dict) else {}
        novelty = reason.get("novelty", 0.0)
        novelty_value = (
            max(0.0, min(1.0, float(novelty))) * 0.16
            if isinstance(novelty, (int, float)) and not isinstance(novelty, bool)
            else 0.0
        )

        need = max(0.0, min(1.0, float(information_need)))
        information_value = 0.0
        if candidate.kind.startswith("scan_"):
            information_value = 0.14 * need
        elif candidate.kind == "inspect_object":
            information_value = 0.10 * max(need, novelty_value / 0.16 if novelty_value else 0.0)
        elif candidate.kind == "explore":
            information_value = 0.06 * need

        damage = memory.recent_damage_signal()
        if candidate.kind in {"survive_damage", "survive_breath"}:
            damage_risk = -0.50 * damage
        else:
            damage_risk = 0.34 * damage

        action_cost = self._COSTS.get(candidate.kind, 0.06)

        # Evidence is deliberately a correction, not the sole objective. This
        # prevents early lucky outcomes from overpowering safety/reflex goals.
        evidence_bonus = 0.18 * (empirical_success - 0.5)
        learned_risk = 0.16 * max(0.0, failure_risk - 0.5)
        total = (
            candidate.priority
            + evidence_bonus
            + information_value
            + novelty_value
            - learned_risk
            - damage_risk
            - action_cost
        )
        if candidate.kind in {"survive_damage", "survive_breath"}:
            total += 1.0

        return UtilityBreakdown(
            total=total,
            base=candidate.priority,
            empirical_success=empirical_success,
            information_value=information_value,
            novelty_value=novelty_value,
            failure_risk=failure_risk,
            damage_risk=damage_risk,
            action_cost=action_cost,
        )
