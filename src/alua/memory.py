from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from .perception import PerceptionFrame


@dataclass(slots=True)
class WorkingMemory:
    capacity: int = 32
    _frames: deque[PerceptionFrame] = field(init=False)

    def __post_init__(self) -> None:
        if self.capacity < 4:
            raise ValueError("working memory capacity must be >= 4")
        self._frames = deque(maxlen=self.capacity)

    def clear(self) -> None:
        self._frames.clear()

    def add(self, frame: PerceptionFrame) -> None:
        self._frames.append(frame)

    @property
    def latest(self) -> PerceptionFrame | None:
        return self._frames[-1] if self._frames else None

    def __len__(self) -> int:
        return len(self._frames)

    def recent_sequences(self) -> tuple[int, ...]:
        return tuple(frame.sequence for frame in self._frames)

    def recent_damage_signal(self, window: int = 4) -> float:
        result = 0.0
        for frame in list(self._frames)[-max(1, window):]:
            contact = frame.persistent.get("channels", {}).get("contact", {})
            value = contact.get("damage_signal", 0)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                result = max(result, float(value))
        return max(0.0, min(1.0, result))
