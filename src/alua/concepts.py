from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .store import Store


@dataclass(frozen=True, slots=True)
class Concept:
    concept_id: str
    members: tuple[str, ...]
    features: tuple[str, ...]
    confidence: float


class ConceptLearner:
    """Forms abstractions from shared empirical affordances.

    Technical item names are never used; only appearance signatures and
    evidence-backed relations participate.
    """

    @staticmethod
    def _fingerprints(store: Store, agent_id: str) -> dict[str, set[str]]:
        result: dict[str, set[str]] = {}
        for belief in store.belief_rows(agent_id, limit=2048):
            subject = belief.get("subject_signature")
            relation = belief.get("relation")
            if not isinstance(subject, str) or not subject:
                continue
            if not isinstance(relation, str) or not relation:
                continue
            support = int(belief.get("support_count", 0))
            contradiction = int(belief.get("contradiction_count", 0))
            confidence = float(belief.get("confidence", 0.5))
            if support <= contradiction or confidence < 0.56:
                continue
            result.setdefault(subject, set()).add(relation)
        return result

    def consolidate(
        self,
        store: Store,
        *,
        agent_id: str,
        sequence: int,
        min_shared_features: int = 2,
    ) -> tuple[Concept, ...]:
        fingerprints = self._fingerprints(store, agent_id)
        groups: dict[tuple[str, ...], list[str]] = {}
        for appearance, features in fingerprints.items():
            if len(features) < min_shared_features:
                continue
            fingerprint = tuple(sorted(features))
            groups.setdefault(fingerprint, []).append(appearance)

        concepts: list[Concept] = []
        for features, members in groups.items():
            if len(members) < 2:
                continue
            encoded = json.dumps(features, separators=(",", ":")).encode()
            concept_id = "concept-" + hashlib.sha256(encoded).hexdigest()[:16]
            confidence = min(
                0.97,
                0.48 + 0.06 * len(members) + 0.04 * len(features),
            )
            payload = {
                "concept_id": concept_id,
                "members": sorted(members)[:64],
                "features": list(features),
                "member_count": len(members),
            }
            store.upsert_cognitive_record(
                agent_id=agent_id,
                record_key=f"concept:{concept_id}",
                record_kind="abstract_concept",
                payload=payload,
                sequence=sequence,
                confidence=confidence,
            )
            concepts.append(
                Concept(
                    concept_id=concept_id,
                    members=tuple(sorted(members)),
                    features=features,
                    confidence=confidence,
                )
            )
        return tuple(
            sorted(
                concepts,
                key=lambda item: (item.confidence, len(item.members)),
                reverse=True,
            )
        )

    def transferable_features(
        self,
        store: Store,
        *,
        agent_id: str,
        appearance_id: str,
    ) -> tuple[tuple[str, float], ...]:
        result: list[tuple[str, float]] = []
        for record in store.cognitive_records(
            agent_id,
            record_kind="abstract_concept",
            limit=256,
        ):
            payload = record["payload"]
            members = payload.get("members")
            features = payload.get("features")
            if not isinstance(members, list) or appearance_id not in members:
                continue
            if not isinstance(features, list):
                continue
            confidence = float(record.get("confidence", 0.5))
            for feature in features:
                if isinstance(feature, str):
                    result.append((feature, confidence))
        result.sort(key=lambda item: item[1], reverse=True)
        return tuple(result)
