from __future__ import annotations

from collections import Counter
from typing import Any


def _longest_streak(values: list[str], expected: str | None = None) -> int:
    longest = 0
    current = 0
    previous: str | None = None
    for value in values:
        if expected is not None:
            current = current + 1 if value == expected else 0
        else:
            current = current + 1 if value == previous else 1
            previous = value
        longest = max(longest, current)
    return longest


def evaluate_trace(trace: list[dict[str, Any]]) -> dict[str, Any]:
    action_types = [str(row.get("action_type") or "") for row in trace]
    goal_kinds = [str(row.get("goal_kind") or "") for row in trace]
    statuses = [str(row.get("status") or "") for row in trace]

    consecutive_look_pairs = 0
    for previous, current in zip(action_types, action_types[1:]):
        if previous == current == "look":
            consecutive_look_pairs += 1

    resolved = [
        row for row in trace
        if row.get("expectation_state") == "resolved"
        and isinstance(row.get("outcome_success"), bool)
    ]
    successful = sum(1 for row in resolved if row["outcome_success"])
    failed = sum(1 for row in resolved if not row["outcome_success"])

    move_resolved = [row for row in resolved if row.get("action_type") == "move"]
    move_successes = sum(1 for row in move_resolved if row["outcome_success"])

    return {
        "decisions": len(trace),
        "action_counts": dict(Counter(action_types)),
        "goal_counts": dict(Counter(goal_kinds)),
        "status_counts": dict(Counter(statuses)),
        "longest_same_action_streak": _longest_streak(action_types),
        "longest_look_streak": _longest_streak(action_types, "look"),
        "consecutive_look_pairs": consecutive_look_pairs,
        "resolved_outcomes": len(resolved),
        "successful_outcomes": successful,
        "failed_outcomes": failed,
        "outcome_success_rate": (
            round(successful / len(resolved), 4) if resolved else None
        ),
        "resolved_moves": len(move_resolved),
        "move_success_rate": (
            round(move_successes / len(move_resolved), 4)
            if move_resolved
            else None
        ),
        "stale_targets": sum(1 for status in statuses if status == "stale_target"),
        "quality_flags": {
            "look_loop_detected": consecutive_look_pairs > 0,
            "action_stereotype_detected": _longest_streak(action_types) >= 8,
            "low_move_success": (
                len(move_resolved) >= 5
                and move_successes / len(move_resolved) < 0.35
            ),
        },
    }
