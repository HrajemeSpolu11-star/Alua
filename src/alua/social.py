from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .perception import PerceptionFrame
from .store import Store


@dataclass(frozen=True, slots=True)
class SocialEntity:
    signature_id: str
    familiarity: float
    trust: float
    encounters: int


class SocialCognition:
    """Evidence model for other agents when a social sensory channel exists.

    The module is intentionally inert if World does not provide such evidence.
    It never classifies an ordinary visual appearance as an agent by guessing.
    """

    def observe(
        self,
        frame: PerceptionFrame,
        store: Store,
        *,
        agent_id: str,
    ) -> tuple[SocialEntity, ...]:
        channels = frame.persistent.get("channels")
        social = channels.get("social") if isinstance(channels, dict) else None
        entities = social.get("entities") if isinstance(social, dict) else None
        if not isinstance(entities, list):
            return ()

        result: list[SocialEntity] = []
        for raw in entities:
            if not isinstance(raw, dict):
                continue
            signature = raw.get("signature_id")
            if not isinstance(signature, str) or not signature:
                continue
            key = f"social:{signature}"
            record = store.cognitive_record(agent_id, key)
            payload = dict(record["payload"]) if record else {}
            encounters = int(payload.get("encounters", 0)) + 1
            cooperative = raw.get("cooperative_signal")
            adverse = raw.get("adverse_signal")
            cooperative = (
                float(cooperative)
                if isinstance(cooperative, (int, float))
                and not isinstance(cooperative, bool)
                else 0.0
            )
            adverse = (
                float(adverse)
                if isinstance(adverse, (int, float))
                and not isinstance(adverse, bool)
                else 0.0
            )
            old_trust = float(payload.get("trust", 0.5))
            evidence = max(-1.0, min(1.0, cooperative - adverse))
            trust = max(
                0.05,
                min(0.95, old_trust * 0.85 + (0.5 + 0.5 * evidence) * 0.15),
            )
            familiarity = min(1.0, encounters / 12.0)
            payload.update(
                {
                    "signature_id": signature,
                    "encounters": encounters,
                    "trust": round(trust, 6),
                    "familiarity": round(familiarity, 6),
                    "last_signal": raw.get("signal")
                    if isinstance(raw.get("signal"), str)
                    else None,
                }
            )
            store.upsert_cognitive_record(
                agent_id=agent_id,
                record_key=key,
                record_kind="social_model",
                payload=payload,
                sequence=frame.sequence,
                confidence=min(0.95, 0.35 + familiarity * 0.6),
            )
            result.append(
                SocialEntity(
                    signature_id=signature,
                    familiarity=familiarity,
                    trust=trust,
                    encounters=encounters,
                )
            )
        return tuple(result)

    def record_claim(
        self,
        store: Store,
        *,
        agent_id: str,
        source_signature: str,
        claim_key: str,
        claim_payload: dict[str, Any],
        sequence: int,
    ) -> dict[str, Any]:
        source = store.cognitive_record(
            agent_id,
            f"social:{source_signature}",
        )
        trust = (
            float(source["payload"].get("trust", 0.5))
            if source
            else 0.35
        )
        # A communicated claim is stored as testimony, never as direct belief.
        return store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key=f"testimony:{source_signature}:{claim_key}",
            record_kind="social_testimony",
            payload={
                "source_signature": source_signature,
                "claim_key": claim_key,
                "claim": claim_payload,
                "source_trust": trust,
                "verified_by_self": False,
            },
            sequence=sequence,
            confidence=min(0.75, trust),
        )
