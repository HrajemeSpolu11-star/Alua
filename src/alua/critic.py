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
    """Lightweight self-critic based on real submitted actions and outcomes.

    It is intentionally model-free and local: it can detect loops and repeated
    failure without receiving any privileged world state.
    """

    def __init__(self) -> None:
        self._actions: deque[tuple[str, str, int]] = deque(maxlen=16)
        self._move_outcomes: deque[bool] = deque(maxlen=8)

    def reset(self) -> None:
        self._actions.clear()
        self._move_outcomes.clear()

    def record_submission(self, action_type: str, goal_kind: str, sequence: int) -> None:
        self._actions.append((action_type, goal_kind, int(sequence)))

    def record_outcome(self, action: dict[str, Any], supported: bool) -> None:
        if action.get("type") == "move":
            self._move_outcomes.append(bool(supported))

    @staticmethod
    def _trailing_count(values: list[str], expected: str) -> int:
        count = 0
        for value in reversed(values):
            if value != expected:
                break
            count += 1
        return count

    def assess(self) -> Critique:
        action_types = [item[0] for item in self._actions]
        goal_kinds = [item[1] for item in self._actions]
        reasons: list[str] = []

        look_streak = self._trailing_count(action_types, "look")
        if look_streak >= 2:
            reasons.append("repeated_look")

        same_action_streak = 0
        if action_types:
            same_action_streak = self._trailing_count(action_types, action_types[-1])
        if same_action_streak >= 5:
            reasons.append("action_stereotype")

        if len(self._move_outcomes) >= 3 and not any(list(self._move_outcomes)[-3:]):
            reasons.append("three_failed_moves")

        recent_moves = list(self._move_outcomes)[-4:]
        if (
            len(goal_kinds) >= 8
            and len(set(goal_kinds[-8:])) == 1
            and len(recent_moves) >= 4
            and sum(1 for value in recent_moves if value) <= 1
        ):
            reasons.append("goal_stagnation")

        return Critique(
            force_replan=bool(reasons),
            suppress_scan=look_streak >= 1,
            reasons=tuple(reasons),
        )
