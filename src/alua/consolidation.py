from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .concepts import ConceptLearner
from .store import Store


@dataclass(frozen=True, slots=True)
class ConsolidationReport:
    sequence: int
    beliefs_decayed: int
    concepts_formed: int
    episode_summary_created: bool


class MemoryConsolidator:
    """Periodic bounded consolidation inspired by sleep-like offline replay."""

    def __init__(self, interval: int = 256) -> None:
        self.interval = max(64, int(interval))
        self._last_sequence = 0
        self.concepts = ConceptLearner()

    def due(self, sequence: int) -> bool:
        return sequence - self._last_sequence >= self.interval

    def consolidate(
        self,
        store: Store,
        *,
        agent_id: str,
        session_id: str,
        sequence: int,
    ) -> ConsolidationReport:
        if not self.due(sequence):
            return ConsolidationReport(sequence, 0, 0, False)

        trace = store.session_trace(agent_id, session_id, limit=128)
        progress_values = [
            float(item["progress_signal"])
            for item in trace
            if isinstance(item.get("progress_signal"), (int, float))
            and not isinstance(item.get("progress_signal"), bool)
        ]
        success_values = [
            1.0 if item["outcome_success"] else 0.0
            for item in trace
            if isinstance(item.get("outcome_success"), bool)
        ]
        action_counts: dict[str, int] = {}
        goal_counts: dict[str, int] = {}
        for item in trace:
            action = item.get("action_type")
            goal = item.get("goal_kind")
            if isinstance(action, str):
                action_counts[action] = action_counts.get(action, 0) + 1
            if isinstance(goal, str):
                goal_counts[goal] = goal_counts.get(goal, 0) + 1

        summary_created = False
        if trace:
            payload: dict[str, Any] = {
                "window_size": len(trace),
                "mean_progress": (
                    round(sum(progress_values) / len(progress_values), 6)
                    if progress_values else None
                ),
                "success_rate": (
                    round(sum(success_values) / len(success_values), 6)
                    if success_values else None
                ),
                "action_counts": action_counts,
                "goal_counts": goal_counts,
                "start_sequence": int(trace[0].get("observation_sequence", sequence)),
                "end_sequence": int(trace[-1].get("observation_sequence", sequence)),
            }
            store.upsert_cognitive_record(
                agent_id=agent_id,
                record_key=f"episode-summary:{session_id}:{sequence // self.interval}",
                record_kind="episodic_summary",
                payload=payload,
                sequence=sequence,
                confidence=min(0.98, 0.5 + len(trace) / 256),
            )
            summary_created = True

        decayed = store.decay_stale_beliefs(
            agent_id,
            before_sequence=max(0, sequence - 2048),
            factor=0.992,
            floor=0.08,
            limit=256,
        )
        concepts = self.concepts.consolidate(
            store,
            agent_id=agent_id,
            sequence=sequence,
        )
        self._last_sequence = sequence
        return ConsolidationReport(
            sequence=sequence,
            beliefs_decayed=decayed,
            concepts_formed=len(concepts),
            episode_summary_created=summary_created,
        )
