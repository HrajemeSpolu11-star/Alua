from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class Critique:
    force_replan: bool
    suppress_scan: bool
    reasons: tuple[str, ...]


class BehaviorCritic:
    """Self-critic over submitted behavior and verified motor progress.

    Replanning is driven by failed or low-quality progress, not merely by the
    fact that the same primitive action type was used repeatedly.
    """

    def __init__(self) -> None:
        self._actions: deque[tuple[str, str, int, str | None]] = deque(maxlen=24)
        self._move_quality: deque[float] = deque(maxlen=12)

    def reset(self) -> None:
        self._actions.clear()
        self._move_quality.clear()

    def record_submission(
        self,
        action_type: str,
        goal_kind: str,
        sequence: int,
        maneuver: str | None = None,
    ) -> None:
        self._actions.append((action_type, goal_kind, int(sequence), maneuver))

    def record_outcome(
        self,
        action: dict[str, Any],
        supported: bool,
        quality: float | None = None,
    ) -> None:
        if action.get("type") != "move":
            return
        if isinstance(quality, (int, float)) and not isinstance(quality, bool):
            value = max(0.0, min(1.0, float(quality)))
        else:
            value = 1.0 if supported else 0.0
        self._move_quality.append(value)

    @staticmethod
    def _trailing_count(values: list[str | None], expected: str | None) -> int:
        count = 0
        for value in reversed(values):
            if value != expected:
                break
            count += 1
        return count

    def assess(self) -> Critique:
        action_types = [item[0] for item in self._actions]
        goal_kinds = [item[1] for item in self._actions]
        maneuvers = [item[3] for item in self._actions]
        reasons: list[str] = []

        look_streak = self._trailing_count(action_types, "look")
        if look_streak >= 2:
            reasons.append("repeated_look")

        recent_quality = list(self._move_quality)
        last_three = recent_quality[-3:]
        if len(last_three) >= 3 and sum(last_three) / len(last_three) < 0.45:
            reasons.append("poor_move_progress")

        last_four = recent_quality[-4:]
        current_maneuver = maneuvers[-1] if maneuvers else None
        maneuver_streak = (
            self._trailing_count(maneuvers, current_maneuver)
            if current_maneuver is not None
            else 0
        )
        if (
            maneuver_streak >= 4
            and len(last_four) >= 3
            and sum(last_four[-3:]) / len(last_four[-3:]) < 0.65
        ):
            reasons.append("maneuver_stereotype")

        if (
            len(goal_kinds) >= 8
            and len(set(goal_kinds[-8:])) == 1
            and len(last_four) >= 4
            and sum(last_four) / len(last_four) < 0.60
        ):
            reasons.append("goal_stagnation")

        return Critique(
            force_replan=bool(reasons),
            suppress_scan=look_streak >= 1,
            reasons=tuple(reasons),
        )
