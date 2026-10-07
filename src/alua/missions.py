from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .store import Store


@dataclass(frozen=True, slots=True)
class Mission:
    key: str
    kind: str
    priority: float
    stage: str
    active: bool
    payload: dict[str, Any]
    confidence: float


class MissionManager:
    """Persistent long-horizon goals that survive short-term interruptions."""

    PREFIX = "mission:"

    def ensure(
        self,
        store: Store,
        *,
        agent_id: str,
        key: str,
        kind: str,
        priority: float,
        sequence: int,
        stage: str = "active",
        payload: dict[str, Any] | None = None,
    ) -> Mission:
        record_key = self.PREFIX + key
        existing = store.cognitive_record(agent_id, record_key)
        body = dict(existing["payload"]) if existing else {}
        if payload:
            body.update(payload)
        body.update(
            {
                "key": key,
                "kind": kind,
                "priority": max(0.0, min(1.5, float(priority))),
                "stage": stage,
                "active": True,
                "last_resumed_sequence": int(sequence),
            }
        )
        record = store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=record_key,
            record_kind="mission",
            payload=body,
            sequence=sequence,
            confidence=max(0.55, float(existing.get("confidence", 0.55)) if existing else 0.55),
        )
        return self._from_record(record)

    def suspend(
        self,
        store: Store,
        *,
        agent_id: str,
        key: str,
        reason: str,
        sequence: int,
    ) -> None:
        record = store.cognitive_record(agent_id, self.PREFIX + key)
        if not record:
            return
        body = dict(record["payload"])
        body["stage"] = "suspended"
        body["active"] = True
        body["suspension_reason"] = reason
        body["suspended_sequence"] = int(sequence)
        store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=self.PREFIX + key,
            record_kind="mission",
            payload=body,
            sequence=sequence,
            confidence=float(record.get("confidence", 0.5)),
        )

    def complete(
        self,
        store: Store,
        *,
        agent_id: str,
        key: str,
        sequence: int,
        supported: bool,
    ) -> None:
        record = store.cognitive_record(agent_id, self.PREFIX + key)
        if not record:
            return
        body = dict(record["payload"])
        body["active"] = False
        body["stage"] = "completed" if supported else "failed"
        body["completed_sequence"] = int(sequence)
        store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=self.PREFIX + key,
            record_kind="mission",
            payload=body,
            sequence=sequence,
            supported=supported,
        )

    def active(
        self,
        store: Store,
        *,
        agent_id: str,
        limit: int = 32,
    ) -> tuple[Mission, ...]:
        missions: list[Mission] = []
        for record in store.cognitive_records(
            agent_id,
            record_kind="mission",
            limit=limit,
        ):
            if record["payload"].get("active") is not True:
                continue
            missions.append(self._from_record(record))
        missions.sort(key=lambda item: (item.priority, item.confidence), reverse=True)
        return tuple(missions)

    @staticmethod
    def _from_record(record: dict[str, Any]) -> Mission:
        body = record["payload"]
        return Mission(
            key=str(body.get("key") or record["record_key"]),
            kind=str(body.get("kind") or "unknown"),
            priority=float(body.get("priority", 0.5)),
            stage=str(body.get("stage") or "active"),
            active=body.get("active") is True,
            payload=dict(body),
            confidence=float(record.get("confidence", 0.5)),
        )
