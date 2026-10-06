from __future__ import annotations

import unittest

from alua.goals import GoalCandidate
from alua.memory import WorkingMemory
from alua.perception import build_frame
from alua.policy import ExplorationPolicy


def frame(sequence: int = 1, damage: float = 0.0):
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {
            "vision": {"rays": [{"distance_fraction": 1.0, "empty": True}]},
            "contact": {"damage_signal": damage},
        },
    })


class PolicyTests(unittest.TestCase):
    def test_inspect_goal_maps_only_to_touch(self) -> None:
        current = frame()
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate(
            key="inspect:p-new",
            kind="inspect_novel",
            priority=0.95,
            target_ref="t1_7",
            target_signature="p-new",
        )
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "manipulate")
        self.assertEqual(action.parameters, {"verb": "touch"})
        self.assertEqual(action.target_ref, "t1_7")

    def test_survival_goal_maps_to_retreat(self) -> None:
        current = frame(damage=0.5)
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate("survive:damage", "survive_damage", 1.0)
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "move")
        self.assertLess(action.parameters["forward"], 0)

    def test_scan_goal_maps_to_relative_look(self) -> None:
        current = frame(sequence=2)
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate("scan:obstacle", "scan_obstacle", 0.8)
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "look")
        self.assertNotEqual(action.parameters["yaw_delta_rad"], 0)

    def test_explore_goal_maps_to_cautious_move(self) -> None:
        current = frame(sequence=3)
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate("explore:open", "explore", 0.5)
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "move")
        self.assertLess(action.parameters["speed_fraction"], 1)


if __name__ == "__main__":
    unittest.main()
