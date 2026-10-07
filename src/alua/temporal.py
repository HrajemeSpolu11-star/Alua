from __future__ import annotations

from dataclasses import dataclass
from collections import deque
from typing import Any

from .store import Store


@dataclass(frozen=True, slots=True)
class TemporalPattern:
    signature: str
    occurrences: int
    mean_interval: float | None
    confidence: float


class TemporalModel:
    """Learns recurrence and recency without assuming external clock semantics."""

    def __init__(self, capacity: int = 128) -> None:
        self._last_time: dict[str, float] = {}
        self._intervals: dict[str, deque[float]] = {}
        self.capacity = max(16, int(capacity))

    def reset_session(self) -> None:
        self._last_time.clear()
        self._intervals.clear()

    def observe(
        self,
        store: Store,
        *,
        agent_id: str,
        signature: str,
        simulation_time: float,
        sequence: int,
    ) -> TemporalPattern:
        previous = self._last_time.get(signature)
        intervals = self._intervals.setdefault(
            signature,
            deque(maxlen=12),
        )
        if previous is not None and simulation_time >= previous:
            intervals.append(simulation_time - previous)
        self._last_time[signature] = simulation_time

        existing = store.cognitive_record(
            agent_id,
            f"temporal:{signature}",
        )
        payload = dict(existing["payload"]) if existing else {}
        occurrences = int(payload.get("occurrences", 0)) + 1
        session_mean = (
            sum(intervals) / len(intervals)
            if intervals
            else None
        )
        old_mean = payload.get("mean_interval")
        if isinstance(old_mean, (int, float)) and session_mean is not None:
            mean_interval = 0.7 * float(old_mean) + 0.3 * session_mean
        else:
            mean_interval = session_mean if session_mean is not None else old_mean
        confidence = min(0.96, occurrences / (occurrences + 6))
        payload.update(
            {
                "signature": signature,
                "occurrences": occurrences,
                "mean_interval": (
                    round(float(mean_interval), 6)
                    if isinstance(mean_interval, (int, float))
                    else None
                ),
                "last_simulation_time": float(simulation_time),
            }
        )
        store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=f"temporal:{signature}",
            record_kind="temporal_pattern",
            payload=payload,
            sequence=sequence,
            confidence=confidence,
        )
        return TemporalPattern(
            signature=signature,
            occurrences=occurrences,
            mean_interval=float(mean_interval)
            if isinstance(mean_interval, (int, float))
            else None,
            confidence=confidence,
        )
