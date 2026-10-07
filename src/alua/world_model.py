from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from .perception import PerceptionFrame, TargetPercept


RAY_SECTORS = {
    0: "front",
    1: "left",
    2: "right",
    3: "down",
    4: "up",
}


@dataclass(slots=True)
class SectorEvidence:
    openness: float = 0.5
    blocked_probability: float = 0.0
    novelty: float = 0.0
    confidence: float = 0.0
    last_sequence: int = 0
    appearance_id: str | None = None
    samples: int = 0

    def update(
        self,
        target: TargetPercept,
        sequence: int,
        novel_appearance_ids: set[str],
        *,
        alpha: float = 0.45,
    ) -> None:
        distance = target.distance_fraction
        observed_open = 0.5 if distance is None else max(0.0, min(1.0, float(distance)))
        blocked = 1.0 if target.blocks_motion is True and observed_open < 0.22 else 0.0
        novel = (
            1.0
            if target.appearance_id is not None
            and target.appearance_id in novel_appearance_ids
            else 0.0
        )
        if self.samples == 0:
            self.openness = observed_open
            self.blocked_probability = blocked
            self.novelty = novel
        else:
            self.openness = (1.0 - alpha) * self.openness + alpha * observed_open
            self.blocked_probability = (
                (1.0 - alpha) * self.blocked_probability + alpha * blocked
            )
            self.novelty = (1.0 - alpha) * self.novelty + alpha * novel
        self.confidence = min(1.0, self.confidence + 0.22)
        self.last_sequence = int(sequence)
        self.appearance_id = target.appearance_id
        self.samples += 1

    def decay(self) -> None:
        self.confidence *= 0.94
        self.novelty *= 0.92


@dataclass(frozen=True, slots=True)
class WorldModelSnapshot:
    sequence: int
    sectors: dict[str, dict[str, Any]]


class EgocentricWorldModel:
    """Bounded local world model built only from Alua's own sensory frames.

    The model deliberately stores no absolute map position and no technical
    object identity. It represents short-lived directional evidence around the
    body, similar to a receding-horizon occupancy model.
    """

    def __init__(self, history_capacity: int = 64):
        if history_capacity < 8:
            raise ValueError("history_capacity must be >= 8")
        self.sectors = {
            name: SectorEvidence()
            for name in ("front", "left", "right", "down", "up")
        }
        self._history: deque[WorldModelSnapshot] = deque(maxlen=history_capacity)
        self.sequence = 0

    def reset(self) -> None:
        for name in self.sectors:
            self.sectors[name] = SectorEvidence()
        self._history.clear()
        self.sequence = 0

    def invalidate_view(self) -> None:
        """Reset directional evidence after a successful head rotation."""
        for name in self.sectors:
            self.sectors[name] = SectorEvidence()

    def update(
        self,
        frame: PerceptionFrame,
        novel_appearance_ids: set[str] | None = None,
    ) -> None:
        novel = novel_appearance_ids or set()
        touched: set[str] = set()
        for target in frame.targets:
            sector = RAY_SECTORS.get(target.ray_index)
            if sector is None:
                continue
            self.sectors[sector].update(target, frame.sequence, novel)
            touched.add(sector)
        for name, evidence in self.sectors.items():
            if name not in touched:
                evidence.decay()
        self.sequence = frame.sequence
        self._history.append(self.snapshot())

    def front_is_blocked(self, threshold: float = 0.55) -> bool:
        front = self.sectors["front"]
        return (
            front.confidence >= 0.20
            and (
                front.blocked_probability >= threshold
                or front.openness <= 0.14
            )
        )

    def sector_score(self, name: str) -> float:
        evidence = self.sectors[name]
        unknown_bonus = 0.18 * (1.0 - evidence.confidence)
        novelty_bonus = 0.24 * evidence.novelty
        blocked_penalty = 0.95 * evidence.blocked_probability
        return (
            0.70 * evidence.openness
            + novelty_bonus
            + unknown_bonus
            - blocked_penalty
        )

    def most_promising_horizontal_sector(self) -> str:
        names = ("front", "left", "right")
        return max(names, key=lambda name: (self.sector_score(name), name))

    def horizontal_uncertainty(self) -> float:
        values = [1.0 - self.sectors[name].confidence for name in ("front", "left", "right")]
        return max(0.0, min(1.0, sum(values) / len(values)))

    def snapshot(self) -> WorldModelSnapshot:
        return WorldModelSnapshot(
            sequence=self.sequence,
            sectors={
                name: {
                    "openness": round(evidence.openness, 6),
                    "blocked_probability": round(evidence.blocked_probability, 6),
                    "novelty": round(evidence.novelty, 6),
                    "confidence": round(evidence.confidence, 6),
                    "last_sequence": evidence.last_sequence,
                    "appearance_id": evidence.appearance_id,
                    "samples": evidence.samples,
                }
                for name, evidence in self.sectors.items()
            },
        )

    def diagnostic_summary(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "front_blocked": self.front_is_blocked(),
            "preferred_sector": self.most_promising_horizontal_sector(),
            "horizontal_uncertainty": round(self.horizontal_uncertainty(), 4),
            "scores": {
                name: round(self.sector_score(name), 4)
                for name in ("front", "left", "right")
            },
        }
