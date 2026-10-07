from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .predictive import action_signature
from .store import Store


@dataclass(frozen=True, slots=True)
class RiskEstimate:
    score: float
    confidence: float
    failures: int
    samples: int


class RiskModel:
    """Learns action risk from failure, slip, damage and poor progress."""

    @staticmethod
    def _key(context_signature: str, action: dict[str, Any]) -> str:
        return f"risk:{context_signature}:{action_signature(action)}"

    def estimate(
        self,
        store: Store,
        *,
        agent_id: str,
        context_signature: str,
        action: dict[str, Any],
    ) -> RiskEstimate:
        record = store.cognitive_record(
            agent_id,
            self._key(context_signature, action),
        )
        if not record:
            return RiskEstimate(0.18, 0.0, 0, 0)
        payload = record["payload"]
        return RiskEstimate(
            score=max(0.0, min(1.0, float(payload.get("risk_score", 0.18)))),
            confidence=float(record.get("confidence", 0.5)),
            failures=int(payload.get("failures", 0)),
            samples=int(payload.get("samples", 0)),
        )

    def learn(
        self,
        store: Store,
        *,
        agent_id: str,
        context_signature: str,
        action: dict[str, Any],
        supported: bool,
        progress: float,
        slip: float,
        damage_signal: float,
        sequence: int,
    ) -> RiskEstimate:
        key = self._key(context_signature, action)
        record = store.cognitive_record(agent_id, key)
        payload = dict(record["payload"]) if record else {}
        samples = int(payload.get("samples", 0)) + 1
        failures = int(payload.get("failures", 0)) + (0 if supported else 1)
        old = float(payload.get("risk_score", 0.18))
        observed = min(
            1.0,
            (0.45 if not supported else 0.0)
            + 0.30 * (1.0 - max(0.0, min(1.0, progress)))
            + 0.15 * max(0.0, min(1.0, slip))
            + 0.65 * max(0.0, min(1.0, damage_signal)),
        )
        alpha = 0.35 if samples < 6 else 0.18
        risk = (1.0 - alpha) * old + alpha * observed
        confidence = min(0.98, samples / (samples + 5))
        payload.update(
            {
                "samples": samples,
                "failures": failures,
                "risk_score": round(risk, 6),
                "last_observed_risk": round(observed, 6),
            }
        )
        store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=key,
            record_kind="risk_model",
            payload=payload,
            sequence=sequence,
            supported=observed < 0.45,
            confidence=confidence,
        )
        return RiskEstimate(risk, confidence, failures, samples)
