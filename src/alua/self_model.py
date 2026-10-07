from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .embodiment import inventory_load, vital_signals
from .predictive import action_signature
from .store import Store


@dataclass(frozen=True, slots=True)
class CapabilityEstimate:
    capability: str
    success_rate: float
    mean_progress: float
    confidence: float
    attempts: int


class SelfModel:
    """Empirical model of the agent's own body and action capabilities."""

    @staticmethod
    def _capability(action: dict[str, Any]) -> str:
        action_type = action.get("type")
        parameters = action.get("parameters")
        parameters = parameters if isinstance(parameters, dict) else {}
        if action_type == "move":
            return f"move:{parameters.get('mode', 'walk')}"
        if action_type in {"interact", "manipulate"}:
            return f"{action_type}:{parameters.get('verb', 'unknown')}"
        return str(action_type or "unknown")

    def learn(
        self,
        store: Store,
        *,
        agent_id: str,
        action: dict[str, Any],
        supported: bool,
        progress: float,
        effort: float,
        sequence: int,
    ) -> CapabilityEstimate:
        capability = self._capability(action)
        key = f"self-capability:{capability}"
        existing = store.cognitive_record(agent_id, key)
        payload = dict(existing["payload"]) if existing else {}
        attempts = int(payload.get("attempts", 0))
        successes = int(payload.get("successes", 0))
        mean_progress = float(payload.get("mean_progress", 0.0))
        mean_effort = float(payload.get("mean_effort", 0.0))

        attempts += 1
        successes += 1 if supported else 0
        progress = max(0.0, min(1.0, float(progress)))
        effort = max(0.0, min(1.0, float(effort)))
        mean_progress += (progress - mean_progress) / attempts
        mean_effort += (effort - mean_effort) / attempts
        success_rate = (successes + 1) / (attempts + 2)
        confidence = min(0.98, attempts / (attempts + 5))

        payload.update(
            {
                "capability": capability,
                "attempts": attempts,
                "successes": successes,
                "success_rate": round(success_rate, 6),
                "mean_progress": round(mean_progress, 6),
                "mean_effort": round(mean_effort, 6),
                "last_action_signature": action_signature(action),
            }
        )
        store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=key,
            record_kind="self_model",
            payload=payload,
            sequence=sequence,
            supported=supported,
            confidence=confidence,
        )
        return CapabilityEstimate(
            capability=capability,
            success_rate=success_rate,
            mean_progress=mean_progress,
            confidence=confidence,
            attempts=attempts,
        )

    def estimate(
        self,
        store: Store,
        agent_id: str,
        capability: str,
    ) -> CapabilityEstimate:
        record = store.cognitive_record(
            agent_id,
            f"self-capability:{capability}",
        )
        if not record:
            return CapabilityEstimate(
                capability=capability,
                success_rate=0.5,
                mean_progress=0.5,
                confidence=0.0,
                attempts=0,
            )
        payload = record["payload"]
        return CapabilityEstimate(
            capability=capability,
            success_rate=float(payload.get("success_rate", 0.5)),
            mean_progress=float(payload.get("mean_progress", 0.5)),
            confidence=float(record.get("confidence", 0.5)),
            attempts=int(payload.get("attempts", 0)),
        )

    @staticmethod
    def body_state(frame: Any) -> dict[str, float]:
        vitals = vital_signals(frame)
        return {
            "health": vitals.health,
            "stamina": vitals.stamina,
            "hunger": vitals.hunger,
            "thirst": vitals.thirst,
            "fatigue": vitals.fatigue,
            "breath": vitals.breath,
            "inventory_load": inventory_load(frame),
        }
