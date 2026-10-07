from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .predictive import action_signature
from .store import Store


@dataclass(frozen=True, slots=True)
class CausalHypothesis:
    key: str
    outcome: str
    mean_effect: float
    confidence: float
    samples: int


class CausalLearner:
    """Intervention-based causal hypotheses.

    A hypothesis means "when I performed action A in context C, effect E
    repeatedly followed". It is not promoted to absolute world truth.
    """

    OUTCOMES = (
        "progress_signal",
        "vertical_progress_signal",
        "nutrition_delta_signal",
        "hydration_delta_signal",
        "stamina_delta_signal",
        "inventory_delta_signal",
    )

    @staticmethod
    def _number(event: dict[str, Any], key: str) -> float:
        value = event.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            return max(-1.0, min(1.0, float(value)))
        return 0.0

    def record_intervention(
        self,
        store: Store,
        *,
        agent_id: str,
        context_signature: str,
        action: dict[str, Any],
        event: dict[str, Any],
        sequence: int,
    ) -> tuple[CausalHypothesis, ...]:
        action_id = action_signature(action)
        result: list[CausalHypothesis] = []
        for outcome in self.OUTCOMES:
            effect = self._number(event, outcome)
            key = f"causal:{context_signature}:{action_id}:{outcome}"
            record = store.cognitive_record(agent_id, key)
            payload = dict(record["payload"]) if record else {}
            samples = int(payload.get("samples", 0)) + 1
            old_mean = float(payload.get("mean_effect", 0.0))
            old_abs = float(payload.get("mean_abs_effect", 0.0))
            mean_effect = old_mean + (effect - old_mean) / samples
            mean_abs = old_abs + (abs(effect) - old_abs) / samples
            consistency = max(
                0.0,
                min(1.0, 1.0 - abs(effect - mean_effect)),
            )
            confidence = min(
                0.97,
                samples / (samples + 5) * (0.55 + 0.45 * consistency),
            )
            payload.update(
                {
                    "context_signature": context_signature,
                    "action_signature": action_id,
                    "outcome": outcome,
                    "samples": samples,
                    "mean_effect": round(mean_effect, 6),
                    "mean_abs_effect": round(mean_abs, 6),
                    "last_effect": round(effect, 6),
                }
            )
            store.upsert_cognitive_record(
                agent_id=agent_id,
                record_key=key,
                record_kind="causal_hypothesis",
                payload=payload,
                sequence=sequence,
                supported=abs(effect) >= 0.01,
                confidence=confidence,
            )
            result.append(
                CausalHypothesis(
                    key=key,
                    outcome=outcome,
                    mean_effect=mean_effect,
                    confidence=confidence,
                    samples=samples,
                )
            )
        return tuple(result)

    def strongest(
        self,
        store: Store,
        *,
        agent_id: str,
        limit: int = 32,
    ) -> tuple[CausalHypothesis, ...]:
        result: list[CausalHypothesis] = []
        for record in store.cognitive_records(
            agent_id,
            record_kind="causal_hypothesis",
            limit=max(32, limit * 4),
        ):
            payload = record["payload"]
            result.append(
                CausalHypothesis(
                    key=record["record_key"],
                    outcome=str(payload.get("outcome", "unknown")),
                    mean_effect=float(payload.get("mean_effect", 0.0)),
                    confidence=float(record.get("confidence", 0.5)),
                    samples=int(payload.get("samples", 0)),
                )
            )
        result.sort(
            key=lambda item: (item.confidence, abs(item.mean_effect), item.samples),
            reverse=True,
        )
        return tuple(result[:limit])
