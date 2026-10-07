from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .perception import PerceptionFrame, TargetPercept
from .store import Store


@dataclass(slots=True)
class ObjectTrack:
    appearance_id: str
    first_sequence: int
    last_sequence: int
    sightings: int
    last_ray: int
    last_distance: float | None
    last_blocks_motion: bool | None
    last_liquid: bool | None
    persistence_confidence: float


class ObjectMemory:
    """Tracks perceptual objects without treating target_ref as identity."""

    def __init__(self, capacity: int = 128) -> None:
        self.capacity = max(16, int(capacity))
        self._tracks: dict[str, ObjectTrack] = {}

    def reset_session(self) -> None:
        for track in self._tracks.values():
            track.persistence_confidence *= 0.65

    def observe(
        self,
        frame: PerceptionFrame,
        store: Store | None = None,
        agent_id: str | None = None,
    ) -> None:
        seen: set[str] = set()
        for target in frame.targets:
            if not target.appearance_id:
                continue
            key = target.appearance_id
            seen.add(key)
            track = self._tracks.get(key)
            if track is None:
                track = ObjectTrack(
                    appearance_id=key,
                    first_sequence=frame.sequence,
                    last_sequence=frame.sequence,
                    sightings=1,
                    last_ray=target.ray_index,
                    last_distance=target.distance_fraction,
                    last_blocks_motion=target.blocks_motion,
                    last_liquid=target.liquid,
                    persistence_confidence=0.55,
                )
                self._tracks[key] = track
            else:
                track.last_sequence = frame.sequence
                track.sightings += 1
                track.last_ray = target.ray_index
                track.last_distance = target.distance_fraction
                track.last_blocks_motion = target.blocks_motion
                track.last_liquid = target.liquid
                track.persistence_confidence = min(
                    0.98,
                    track.persistence_confidence + 0.08,
                )

            if store is not None and agent_id is not None:
                store.upsert_cognitive_record(
                    agent_id=agent_id,
                    record_key=f"object:{key}",
                    record_kind="object_concept",
                    payload={
                        "appearance_id": key,
                        "sightings": track.sightings,
                        "last_ray": track.last_ray,
                        "last_distance": track.last_distance,
                        "blocks_motion": track.last_blocks_motion,
                        "liquid": track.last_liquid,
                    },
                    sequence=frame.sequence,
                    confidence=track.persistence_confidence,
                )

        for key, track in list(self._tracks.items()):
            if key not in seen:
                age = max(0, frame.sequence - track.last_sequence)
                track.persistence_confidence *= 0.985 ** min(age, 16)
            if track.persistence_confidence < 0.08:
                del self._tracks[key]

        if len(self._tracks) > self.capacity:
            keep = sorted(
                self._tracks.values(),
                key=lambda item: (
                    item.persistence_confidence,
                    item.last_sequence,
                ),
                reverse=True,
            )[: self.capacity]
            self._tracks = {item.appearance_id: item for item in keep}

    def track(self, appearance_id: str) -> ObjectTrack | None:
        return self._tracks.get(appearance_id)

    def remembered(self, *, min_confidence: float = 0.25) -> tuple[ObjectTrack, ...]:
        return tuple(
            sorted(
                (
                    item
                    for item in self._tracks.values()
                    if item.persistence_confidence >= min_confidence
                ),
                key=lambda item: (
                    item.persistence_confidence,
                    item.last_sequence,
                ),
                reverse=True,
            )
        )

    @staticmethod
    def best_visual_target(
        frame: PerceptionFrame,
        appearance_id: str,
    ) -> TargetPercept | None:
        candidates = [
            target
            for target in frame.targets
            if target.appearance_id == appearance_id
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda item: (
                item.distance_fraction
                if item.distance_fraction is not None
                else 1.0,
                item.ray_index,
            ),
        )

    def diagnostics(self) -> dict[str, Any]:
        remembered = self.remembered()
        return {
            "tracked_objects": len(self._tracks),
            "persistent_objects": len(remembered),
            "top": [
                {
                    "appearance_id": item.appearance_id,
                    "confidence": round(item.persistence_confidence, 4),
                    "sightings": item.sightings,
                    "last_sequence": item.last_sequence,
                }
                for item in remembered[:8]
            ],
        }
