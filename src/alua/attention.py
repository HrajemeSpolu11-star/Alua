from __future__ import annotations

from dataclasses import dataclass

from .perception import PerceptionFrame


@dataclass(frozen=True, slots=True)
class AttentionState:
    focus_kind: str
    focus_signature: str | None
    focus_ray: int | None
    salience: float
    surprise: float
    uncertainty: float


class AttentionSystem:
    def __init__(self) -> None:
        self._previous: dict[int, tuple[str | None, float | None, bool | None]] = {}

    def reset_session(self) -> None:
        self._previous.clear()

    def assess(self, frame: PerceptionFrame, novel_ids: set[str] | None = None) -> AttentionState:
        novel_ids = novel_ids or set()
        best = (0.10, None, None)
        changed = 0
        current: dict[int, tuple[str | None, float | None, bool | None]] = {}
        for target in frame.targets:
            snapshot = (target.appearance_id, target.distance_fraction, target.blocks_motion)
            if target.ray_index in self._previous and self._previous[target.ray_index] != snapshot:
                changed += 1
            current[target.ray_index] = snapshot
            score = 0.10
            if target.appearance_id and target.appearance_id in novel_ids:
                score += 0.40
            if target.distance_fraction is not None:
                score += 0.20 * (1.0 - max(0.0, min(1.0, target.distance_fraction)))
            if target.blocks_motion is True:
                score += 0.12
            if score > best[0]:
                best = (min(1.0, score), target.appearance_id, target.ray_index)
        self._previous = current
        denominator = max(1, len(frame.targets))
        return AttentionState(
            focus_kind="visual" if best[1] is not None else "ambient",
            focus_signature=best[1],
            focus_ray=best[2],
            salience=best[0],
            surprise=min(1.0, changed / denominator),
            uncertainty=max(0.0, min(1.0, 1.0 - len(current) / 5.0)),
        )
