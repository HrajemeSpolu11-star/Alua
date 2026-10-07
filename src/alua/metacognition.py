from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MetaState:
    stagnation: float
    loop_risk: float
    uncertainty: float
    prediction_surprise: float
    confidence: float
    recommended_mode: str
    reasons: tuple[str, ...]


class Metacognition:
    """Monitors cognition itself without inventing world truth."""

    def __init__(self) -> None:
        self._progress: deque[float] = deque(maxlen=16)
        self._places: deque[str] = deque(maxlen=18)
        self._actions: deque[str] = deque(maxlen=18)
        self._prediction_errors: deque[float] = deque(maxlen=12)

    def reset_session(self) -> None:
        self._progress.clear()
        self._places.clear()
        self._actions.clear()
        self._prediction_errors.clear()

    def observe_place(self, signature: str) -> None:
        self._places.append(signature)

    def record_action(self, action: dict[str, Any]) -> None:
        action_type = str(action.get("type") or "unknown")
        parameters = action.get("parameters")
        parameters = parameters if isinstance(parameters, dict) else {}
        if action_type == "move":
            action_type = f"move:{parameters.get('mode', 'walk')}"
        elif action_type in {"interact", "manipulate"}:
            action_type = f"{action_type}:{parameters.get('verb', 'unknown')}"
        self._actions.append(action_type)

    def record_outcome(
        self,
        *,
        progress: float,
        prediction_error: float | None = None,
    ) -> None:
        self._progress.append(max(0.0, min(1.0, float(progress))))
        if prediction_error is not None:
            self._prediction_errors.append(
                max(0.0, min(1.0, float(prediction_error)))
            )

    @staticmethod
    def _trailing_same(values: deque[str]) -> int:
        if not values:
            return 0
        expected = values[-1]
        count = 0
        for value in reversed(values):
            if value != expected:
                break
            count += 1
        return count

    def assess(
        self,
        *,
        sensory_uncertainty: float,
        topology_revisit_ratio: float,
        dead_end_score: float,
    ) -> MetaState:
        if self._progress:
            recent_progress = sum(self._progress) / len(self._progress)
        else:
            recent_progress = 0.5
        low_progress = max(0.0, min(1.0, (0.58 - recent_progress) / 0.58))

        place_loop = 0.0
        if len(self._places) >= 6:
            unique = len(set(self._places))
            place_loop = max(0.0, 1.0 - unique / len(self._places))

        action_repeat = min(
            1.0,
            max(0, self._trailing_same(self._actions) - 2) / 6.0,
        )
        loop_risk = min(
            1.0,
            0.55 * max(place_loop, topology_revisit_ratio)
            + 0.45 * action_repeat,
        )

        prediction_surprise = (
            sum(self._prediction_errors) / len(self._prediction_errors)
            if self._prediction_errors
            else 0.0
        )
        stagnation = min(
            1.0,
            0.48 * low_progress
            + 0.32 * loop_risk
            + 0.20 * dead_end_score,
        )
        uncertainty = max(
            0.0,
            min(1.0, float(sensory_uncertainty)),
        )

        reasons: list[str] = []
        if dead_end_score >= 0.62:
            reasons.append("dead_end_evidence")
        if low_progress >= 0.55:
            reasons.append("low_progress")
        if loop_risk >= 0.55:
            reasons.append("revisit_loop")
        if prediction_surprise >= 0.45:
            reasons.append("model_prediction_error")
        if uncertainty >= 0.60:
            reasons.append("high_uncertainty")

        if dead_end_score >= 0.62 or stagnation >= 0.68:
            mode = "backtrack"
        elif prediction_surprise >= 0.55:
            mode = "reconsider_model"
        elif uncertainty >= 0.62:
            mode = "seek_information"
        elif recent_progress >= 0.68:
            mode = "continue"
        else:
            mode = "explore"

        confidence = min(
            1.0,
            0.35
            + 0.35 * min(1.0, len(self._progress) / 8.0)
            + 0.30 * min(1.0, len(self._places) / 8.0),
        )
        return MetaState(
            stagnation=stagnation,
            loop_risk=loop_risk,
            uncertainty=uncertainty,
            prediction_surprise=prediction_surprise,
            confidence=confidence,
            recommended_mode=mode,
            reasons=tuple(reasons),
        )
