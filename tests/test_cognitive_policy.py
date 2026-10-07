from __future__ import annotations

import unittest

from alua.goals import GoalCandidate
from alua.memory import WorkingMemory
from alua.perception import build_frame
from alua.policy import ExplorationPolicy


def make_frame():
    return build_frame({"schema_version":1,"agent_id":"alua:1","sequence":1,"simulation_time":1.0,"channels":{"vision":{"rays":[]}}})


class CognitivePolicyTests(unittest.TestCase):
    def test_route_return_turn(self) -> None:
        current = make_frame()
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate("spatial:backtrack:p", "spatial_backtrack", 1.0, reason={"phase":"turn","yaw_delta_rad":-0.6,"target_place":"p"})
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "look")
        self.assertAlmostEqual(action.parameters["yaw_delta_rad"], -0.6)

    def test_route_return_move(self) -> None:
        current = make_frame()
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate("spatial:backtrack:p", "spatial_backtrack", 1.0, reason={"phase":"move","maneuver":"back","target_place":"p"})
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "move")
        self.assertLess(action.parameters["forward"], 0)

    def test_model_selected_move(self) -> None:
        current = make_frame()
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate("deliberate:p", "deliberate_navigation", 0.9, reason={"action":{"type":"move","parameters":{"mode":"walk","forward":0.15,"strafe":0.75,"vertical":0.0,"duration_s":0.32,"speed_fraction":0.42}},"deliberation":{"score":0.8}})
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "move")
        self.assertGreater(action.parameters["strafe"], 0)


if __name__ == "__main__":
    unittest.main()
