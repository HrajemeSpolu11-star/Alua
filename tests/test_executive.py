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

    def test_low_progress_stagnation_reorients_then_keeps_escape_plan(self) -> None:
        controller = ExecutiveController()
        current = frame(10, blocked=True)
        memory = WorkingMemory()
        memory.add(current)
        controller.observe(current)
        goal = GoalCandidate("explore:open", "explore", 0.5)
        failed_action = {
            "type": "move",
            "parameters": {"forward": 1.0, "strafe": 0.0},
        }
        for sequence in range(7, 10):
            controller.critic.record_submission(
                "move",
                "explore",
                sequence,
                maneuver="forward",
            )
            controller.critic.record_outcome(
                failed_action,
                False,
                quality=0.25,
            )

        first = controller.choose(current, goal, memory)
        self.assertEqual(first.action_type, "look")
        self.assertEqual(first.rationale["plan_skill"], "escape_stagnation")
        self.assertEqual(first.rationale["plan_step"], "reorient_escape")

        controller.on_submitted(first, goal, 10)
        controller.on_outcome(
            {
                "goal_key": "explore:open",
                "goal_kind": "explore",
                "action": {
                    "type": "look",
                    "parameters": first.parameters,
                },
            },
            True,
            quality=1.0,
        )

        next_frame = frame(11, blocked=False)
        memory.add(next_frame)
        controller.observe(next_frame)
        second = controller.choose(next_frame, goal, memory)
        self.assertEqual(second.action_type, "move")
        self.assertEqual(second.rationale["plan_skill"], "escape_stagnation")
        self.assertEqual(second.rationale["plan_step"], "navigate_escape")

    def test_thirst_search_bypasses_blocked_front_using_local_navigation(self) -> None:
        # Regression from live Android benchmark: 175/226 decisions were
        # thirst-driven, but the old need/search plan always moved forward.
        controller = ExecutiveController()
        current = frame(101, blocked=True)
        memory = WorkingMemory()
        memory.add(current)
        controller.observe(current, {"left"})
        goal = GoalCandidate(
            "need:thirst:search", "satisfy_thirst", 0.9,
            reason={"phase": "search", "selector": "body_need"},
        )

        intent = controller.choose(current, goal, memory)
        self.assertEqual(intent.action_type, "move")
        self.assertEqual(intent.rationale["plan_skill"], "bypass_obstacle")
        self.assertEqual(intent.rationale["plan_step"], "navigate_lateral")
        self.assertEqual(intent.rationale["policy"], "hierarchical_local_navigation")
        self.assertLess(intent.parameters["strafe"], 0.0)
        self.assertLess(intent.parameters["forward"], 0.5)

    def test_hunger_search_uses_escape_after_verified_low_progress(self) -> None:
        controller = ExecutiveController()
        current = frame(110, blocked=True)
        memory = WorkingMemory()
        memory.add(current)
        controller.observe(current)
        goal = GoalCandidate(
            "need:hunger:search", "satisfy_hunger", 0.9,
            reason={"phase": "search"},
        )
        failed_action = {
            "type": "move",
            "parameters": {"mode": "walk", "forward": 1.0, "strafe": 0.0},
        }
        for sequence in range(107, 110):
            controller.critic.record_submission(
                "move", "satisfy_hunger", sequence, maneuver="forward",
            )
            controller.critic.record_outcome(
                failed_action, False, quality=0.05,
            )

        intent = controller.choose(current, goal, memory)
        self.assertEqual(intent.action_type, "look")
        self.assertEqual(intent.rationale["plan_skill"], "escape_stagnation")
        self.assertEqual(intent.rationale["plan_step"], "reorient_escape")

        controller.on_submitted(intent, goal, 110)
        controller.on_outcome(
            {"goal_key": goal.key, "goal_kind": goal.kind,
             "action": {"type": "look", "parameters": intent.parameters}},
            True,
            quality=1.0,
        )
        next_frame = frame(111, blocked=False)
        memory.add(next_frame)
        controller.observe(next_frame)
        next_intent = controller.choose(next_frame, goal, memory)
        self.assertEqual(next_intent.action_type, "move")
        self.assertEqual(next_intent.rationale["plan_skill"], "escape_stagnation")
        self.assertEqual(next_intent.rationale["plan_step"], "navigate_escape")

    def test_need_with_visible_resource_still_uses_body_need_plan(self) -> None:
        controller = ExecutiveController()
        current = frame(120, blocked=True)
        memory = WorkingMemory()
        memory.add(current)
        controller.observe(current)
        goal = GoalCandidate(
            "need:drink:p12", "satisfy_thirst", 0.9,
            target_ref="t120_1", target_signature="p12",
            reason={"phase": "drink"},
        )
        self.assertEqual(
            controller._current_plan(goal, current).skill_name,
            "satisfy_body_need",
        )

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
