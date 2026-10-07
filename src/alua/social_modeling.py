from __future__ import annotations

from dataclasses import dataclass

from .store import Store


@dataclass(frozen=True, slots=True)
class PeerBehavior:
    signature_id: str
    likely_action: str | None
    confidence: float
    observations: int


class PeerBehaviorModel:
    def observe(self, store: Store, *, agent_id: str, peer_signature: str, action_kind: str | None, sequence: int) -> PeerBehavior:
        key = f"peer:{peer_signature}"
        record = store.cognitive_record(agent_id, key)
        payload = dict(record["payload"]) if record else {}
        observations = int(payload.get("observations", 0)) + 1
        counts = dict(payload.get("action_counts", {}))
        if action_kind:
            counts[action_kind] = int(counts.get(action_kind, 0)) + 1
        likely = max(counts, key=counts.get) if counts else None
        dominant = max(counts.values()) / max(1, sum(counts.values())) if counts else 0.0
        confidence = min(0.92, observations / (observations + 8) * (0.55 + 0.45 * dominant))
        payload.update({"signature_id": peer_signature, "observations": observations, "action_counts": counts, "likely_action": likely})
        store.upsert_cognitive_record(agent_id=agent_id, record_key=key, record_kind="peer_behavior_model", payload=payload, sequence=sequence, confidence=confidence)
        return PeerBehavior(peer_signature, likely, confidence, observations)
