from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .store import Store


@dataclass(frozen=True, slots=True)
class ProspectiveIntent:
    key: str
    kind: str
    trigger_place: str | None
    priority: float
    payload: dict[str, Any]
    confidence: float


class ProspectiveMemory:
    """Persistent 'remember to do X when Y becomes true' memory."""

    PREFIX = "prospective:"

    def remember(
        self,
        store: Store,
        *,
        agent_id: str,
        key: str,
        kind: str,
        sequence: int,
        trigger_place: str | None = None,
        priority: float = 0.5,
        payload: dict[str, Any] | None = None,
    ) -> ProspectiveIntent:
        record_key = self.PREFIX + key
        body = dict(payload or {})
        body.update(
            {
                "key": key,
                "kind": kind,
                "trigger_place": trigger_place,
                "priority": max(0.0, min(1.5, float(priority))),
                "active": True,
            }
        )
        record = store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=record_key,
            record_kind="prospective_intent",
            payload=body,
            sequence=sequence,
            confidence=0.72,
        )
        return self._from_record(record)

    def complete(
        self,
        store: Store,
        *,
        agent_id: str,
        key: str,
        sequence: int,
        supported: bool,
    ) -> None:
        record_key = self.PREFIX + key
        record = store.cognitive_record(agent_id, record_key)
        if not record:
            return
        payload = dict(record["payload"])
        payload["active"] = False
        payload["completed_sequence"] = int(sequence)
        payload["completed_successfully"] = bool(supported)
        store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=record_key,
            record_kind="prospective_intent",
            payload=payload,
            sequence=sequence,
            supported=supported,
        )

    def due(
        self,
        store: Store,
        *,
        agent_id: str,
        current_place: str | None,
        limit: int = 32,
    ) -> tuple[ProspectiveIntent, ...]:
        result: list[ProspectiveIntent] = []
        for record in store.cognitive_records(
            agent_id,
            record_kind="prospective_intent",
            limit=limit,
        ):
            payload = record["payload"]
            if payload.get("active") is not True:
                continue
            trigger = payload.get("trigger_place")
            if trigger is not None and trigger != current_place:
                continue
            result.append(self._from_record(record))
        result.sort(key=lambda item: (item.priority, item.confidence), reverse=True)
        return tuple(result)

    @staticmethod
    def _from_record(record: dict[str, Any]) -> ProspectiveIntent:
        payload = record["payload"]
        return ProspectiveIntent(
            key=str(payload.get("key") or record["record_key"]),
            kind=str(payload.get("kind") or "unknown"),
            trigger_place=payload.get("trigger_place")
            if isinstance(payload.get("trigger_place"), str)
            else None,
            priority=float(payload.get("priority", 0.5)),
            payload=dict(payload),
            confidence=float(record.get("confidence", 0.5)),
        )
