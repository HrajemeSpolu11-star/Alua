from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .predictive import action_signature
from .store import Store


@dataclass(frozen=True, slots=True)
class StrategyEstimate:
    score: float
    confidence: float
    attempts: int


class StrategyLearner:
    """Learns context-light strategy priors from repeated goal outcomes.

    This is deliberately weaker than context-specific prediction. It provides
    transfer hints when Alua meets a new context with little direct evidence.
    """

    @staticmethod
    def _key(goal_kind: str, action: dict[str, Any]) -> str:
        return f"strategy:{goal_kind}:{action_signature(action)}"

    def learn(
        self,
        store: Store,
        *,
        agent_id: str,
        goal_kind: str,
        action: dict[str, Any],
        supported: bool,
        progress: float,
        sequence: int,
    ) -> StrategyEstimate:
        key = self._key(goal_kind, action)
        record = store.cognitive_record(agent_id, key)
        payload = dict(record["payload"]) if record else {}
        attempts = int(payload.get("attempts", 0)) + 1
        successes = int(payload.get("successes", 0)) + (1 if supported else 0)
        old_progress = float(payload.get("mean_progress", 0.5))
        progress = max(0.0, min(1.0, float(progress)))
        mean_progress = old_progress + (progress - old_progress) / attempts
        success_rate = (successes + 1) / (attempts + 2)
        score = 0.58 * mean_progress + 0.42 * success_rate
        confidence = min(0.95, attempts / (attempts + 8))
        payload.update(
            {
                "goal_kind": goal_kind,
                "action_signature": action_signature(action),
                "attempts": attempts,
                "successes": successes,
                "mean_progress": round(mean_progress, 6),
                "success_rate": round(success_rate, 6),
                "strategy_score": round(score, 6),
            }
        )
        store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=key,
            record_kind="strategy_model",
            payload=payload,
            sequence=sequence,
            supported=supported,
            confidence=confidence,
        )
        return StrategyEstimate(score, confidence, attempts)

    def estimate(
        self,
        store: Store,
        *,
        agent_id: str,
        goal_kind: str,
        action: dict[str, Any],
    ) -> StrategyEstimate:
        record = store.cognitive_record(
            agent_id,
            self._key(goal_kind, action),
        )
        if not record:
            return StrategyEstimate(0.5, 0.0, 0)
        payload = record["payload"]
        return StrategyEstimate(
            score=float(payload.get("strategy_score", 0.5)),
            confidence=float(record.get("confidence", 0.5)),
            attempts=int(payload.get("attempts", 0)),
        )
