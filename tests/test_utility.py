from __future__ import annotations

import unittest

from alua.goals import GoalCandidate
from alua.memory import WorkingMemory
from alua.perception import build_frame
from alua.utility import AdaptiveUtilityModel


def make_memory(*, damage: float = 0.0) -> WorkingMemory:
    frame = build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": 1,
        "simulation_time": 1.0,
        "channels": {
            "contact": {"damage_signal": damage},
            "vision": {"rays": [{"distance_fraction": 1.0, "empty": True}]},
        },
    })
    memory = WorkingMemory()
    memory.add(frame)
    return memory


class UtilityTests(unittest.TestCase):
    def test_novel_information_goal_receives_information_value(self) -> None:
        model = AdaptiveUtilityModel()
        goal = GoalCandidate(
            "inspect:p-new",
            "inspect_object",
            0.80,
            reason={"novelty": 1.0},
        )
        score = model.evaluate(
            goal,
            stats=None,
            memory=make_memory(),
            information_need=0.9,
        )
        self.assertGreater(score.information_value, 0)
        self.assertGreater(score.novelty_value, 0)
        self.assertGreater(score.total, score.base)

    def test_recent_damage_penalizes_non_survival_but_boosts_survival(self) -> None:
        model = AdaptiveUtilityModel()
        memory = make_memory(damage=0.8)
        explore = model.evaluate(
            GoalCandidate("explore:open", "explore", 0.5),
            stats=None,
            memory=memory,
            information_need=0.2,
        )
        survive = model.evaluate(
            GoalCandidate("survive:damage", "survive_damage", 1.0),
            stats=None,
            memory=memory,
            information_need=0.2,
        )
        self.assertGreater(explore.damage_risk, 0)
        self.assertLess(survive.damage_risk, 0)
        self.assertGreater(survive.total, explore.total)

    def test_repeated_failures_reduce_goal_utility(self) -> None:
        model = AdaptiveUtilityModel()
        memory = make_memory()
        candidate = GoalCandidate("explore:open", "explore", 0.5)
        reliable = model.evaluate(
            candidate,
            stats={"attempts": 8, "successes": 7, "failures": 1},
            memory=memory,
            information_need=0.2,
        )
        unreliable = model.evaluate(
            candidate,
            stats={"attempts": 8, "successes": 1, "failures": 7},
            memory=memory,
            information_need=0.2,
        )
        self.assertGreater(reliable.total, unreliable.total)


if __name__ == "__main__":
    unittest.main()
