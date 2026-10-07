from __future__ import annotations

import unittest

from alua.executive import ExecutiveController
from alua.goals import GoalCandidate
from alua.memory import WorkingMemory
from alua.perception import build_frame


def frame(sequence: int, *, blocked: bool) -> object:
    if blocked:
        rays = [
            {"distance_fraction": 0.06, "appearance_id": "front", "blocks_motion": True},
            {"distance_fraction": 0.92, "appearance_id": "left", "blocks_motion": False},
            {"distance_fraction": 0.55, "appearance_id": "right", "blocks_motion": False},
        ]
    else:
        rays = [
            {"distance_fraction": 1.0, "empty": True},
            {"distance_fraction": 0.6, "appearance_id": "left", "blocks_motion": False},
            {"distance_fraction": 0.6, "appearance_id": "right", "blocks_motion": False},
        ]
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {"vision": {"rays": rays}},
    })


class ExecutiveTests(unittest.TestCase):
    def test_blocked_explore_uses_hierarchical_bypass_plan(self) -> None:
        controller = ExecutiveController()
        current = frame(1, blocked=True)
        memory = WorkingMemory()
        memory.add(current)
        controller.observe(current, {"left"})
        goal = GoalCandidate("explore:open", "explore", 0.5)

        intent = controller.choose(current, goal, memory)
        self.assertEqual(intent.action_type, "move")
        self.assertEqual(intent.rationale["plan_skill"], "bypass_obstacle")
        self.assertEqual(intent.rationale["plan_step"], "navigate_lateral")
        self.assertNotEqual(intent.parameters["strafe"], 0.0)

    def test_successful_first_macro_step_advances_plan(self) -> None:
        controller = ExecutiveController()
        current = frame(1, blocked=True)
        memory = WorkingMemory()
        memory.add(current)
        controller.observe(current)
        goal = GoalCandidate("explore:open", "explore", 0.5)
        first = controller.choose(current, goal, memory)

        controller.on_submitted(first, goal, 1)
        controller.on_outcome(
            {
                "goal_key": "explore:open",
                "goal_kind": "explore",
                "action": {
                    "type": "move",
                    "parameters": first.parameters,
                },
            },
            True,
        )

        next_frame = frame(2, blocked=False)
        memory.add(next_frame)
        controller.observe(next_frame)
        second = controller.choose(next_frame, goal, memory)
        self.assertEqual(second.rationale["plan_step_index"], 1)
        self.assertEqual(second.rationale["plan_step"], "navigate_frontier")

    def test_session_reset_clears_local_plan_and_navigation_history(self) -> None:
        controller = ExecutiveController()
        current = frame(1, blocked=True)
        memory = WorkingMemory()
        memory.add(current)
        controller.observe(current)
        goal = GoalCandidate("explore:open", "explore", 0.5)
        controller.choose(current, goal, memory)
        self.assertIsNotNone(controller.active_plan)
        controller.reset_session()
        self.assertIsNone(controller.active_plan)
        self.assertEqual(controller.world_model.sequence, 0)


if __name__ == "__main__":
    unittest.main()
