from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .navigation import LocalNavigator
from .store import Store


def action_signature(action: dict[str, Any]) -> str:
    action_type = action.get("type")
    parameters = action.get("parameters")
    parameters = parameters if isinstance(parameters, dict) else {}
    payload: dict[str, Any] = {"type": action_type}
    if action_type == "move":
        payload["mode"] = parameters.get("mode", "walk")
        payload["maneuver"] = LocalNavigator.maneuver_from_parameters(parameters)
    elif action_type in {"interact", "manipulate"}:
        payload["verb"] = parameters.get("verb")
    elif action_type == "look":
        yaw = parameters.get("yaw_delta_rad", 0.0)
        pitch = parameters.get("pitch_delta_rad", 0.0)
        payload["yaw_sign"] = 1 if isinstance(yaw, (int, float)) and yaw > 0.05 else (-1 if isinstance(yaw, (int, float)) and yaw < -0.05 else 0)
        payload["pitch_sign"] = 1 if isinstance(pitch, (int, float)) and pitch > 0.05 else (-1 if isinstance(pitch, (int, float)) and pitch < -0.05 else 0)
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()
    return "act-" + hashlib.sha256(encoded).hexdigest()[:16]


@dataclass(frozen=True, slots=True)
class Prediction:
    expected_progress: float
    expected_success: float
    confidence: float
    evidence_count: int


@dataclass(frozen=True, slots=True)
class PredictionOutcome:
    error: float
    surprise: float
    expected_progress: float
    observed_progress: float
    confidence_before: float


class PredictiveModel:
    """Learns action consequences from interventions made by this agent."""

    def __init__(self) -> None:
        self.last_error = 0.0
        self.last_surprise = 0.0

    @staticmethod
    def _key(context_signature: str, action: dict[str, Any]) -> str:
        return f"prediction:{context_signature}:{action_signature(action)}"

    def predict(
        self,
        store: Store,
        agent_id: str,
        context_signature: str,
        action: dict[str, Any],
    ) -> Prediction:
        record = store.cognitive_record(
            agent_id,
            self._key(context_signature, action),
        )
        if not record:
            return Prediction(
                expected_progress=0.5,
                expected_success=0.5,
                confidence=0.0,
                evidence_count=0,
            )
        payload = record["payload"]
        return Prediction(
            expected_progress=float(payload.get("mean_progress", 0.5)),
            expected_success=float(payload.get("success_rate", 0.5)),
            confidence=float(record.get("confidence", 0.5)),
            evidence_count=int(payload.get("samples", 0)),
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
        sequence: int,
    ) -> PredictionOutcome:
        progress = max(0.0, min(1.0, float(progress)))
        key = self._key(context_signature, action)
        existing = store.cognitive_record(agent_id, key)
        if existing:
            payload = dict(existing["payload"])
            samples = int(payload.get("samples", 0))
            mean_progress = float(payload.get("mean_progress", 0.5))
            successes = int(payload.get("successes", 0))
            confidence_before = float(existing.get("confidence", 0.5))
        else:
            payload = {}
            samples = 0
            mean_progress = 0.5
            successes = 0
            confidence_before = 0.0

        error = abs(progress - mean_progress)
        new_samples = samples + 1
        new_mean = (mean_progress * samples + progress) / new_samples
        new_successes = successes + (1 if supported else 0)
        success_rate = (new_successes + 1) / (new_samples + 2)
        confidence = min(0.98, new_samples / (new_samples + 4))

        payload.update(
            {
                "context_signature": context_signature,
                "action_signature": action_signature(action),
                "samples": new_samples,
                "mean_progress": round(new_mean, 6),
                "successes": new_successes,
                "success_rate": round(success_rate, 6),
                "last_prediction_error": round(error, 6),
            }
        )
        store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=key,
            record_kind="predictive_model",
            payload=payload,
            sequence=sequence,
            supported=supported,
            confidence=confidence,
        )
        surprise = min(
            1.0,
            error * (0.45 + 0.55 * max(confidence_before, 0.2)),
        )
        self.last_error = error
        self.last_surprise = surprise
        return PredictionOutcome(
            error=error,
            surprise=surprise,
            expected_progress=mean_progress,
            observed_progress=progress,
            confidence_before=confidence_before,
        )

    def counterfactual_scores(
        self,
        store: Store,
        *,
        agent_id: str,
        context_signature: str,
        actions: list[dict[str, Any]],
        risk_penalties: dict[str, float] | None = None,
    ) -> list[tuple[dict[str, Any], float, Prediction]]:
        risks = risk_penalties or {}
        result: list[tuple[dict[str, Any], float, Prediction]] = []
        for action in actions:
            prediction = self.predict(
                store,
                agent_id,
                context_signature,
                action,
            )
            signature = action_signature(action)
            information_bonus = 0.18 * (1.0 - prediction.confidence)
            risk = max(0.0, float(risks.get(signature, 0.0)))
            score = (
                0.58 * prediction.expected_progress
                + 0.24 * prediction.expected_success
                + information_bonus
                - 0.45 * risk
            )
            result.append((action, score, prediction))
        result.sort(key=lambda item: item[1], reverse=True)
        return result
