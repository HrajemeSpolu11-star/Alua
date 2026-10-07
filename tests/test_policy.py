from __future__ import annotations

import unittest

from alua.goals import GoalCandidate
from alua.memory import WorkingMemory
from alua.perception import build_frame
from alua.policy import ExplorationPolicy


def frame(
    sequence: int = 1,
    damage: float = 0.0,
    right_occupied: float = 0.0,
    blocked: bool = False,
):
    ray = {"distance_fraction": 1.0, "empty": True}
    if blocked:
        ray = {
            "distance_fraction": 0.08,
            "appearance_id": "p-wall",
            "blocks_motion": True,
            "liquid": False,
        }
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {
            "vision": {"rays": [ray]},
            "contact": {"damage_signal": damage},
            "body_schema": {
                "schema_version": 1,
                "effectors": {
                    "hand_right": {
                        "present_signal": 1.0,
                        "touch_signal": 1.0,
                        "grasp_signal": 1.0,
                        "occupied_signal": right_occupied,
                    },
                    "hand_left": {
                        "present_signal": 1.0,
                        "touch_signal": 1.0,
                        "grasp_signal": 1.0,
                        "occupied_signal": 0.0,
                    },
                },
            },
        },
    })


class PolicyTests(unittest.TestCase):
    def test_inspect_goal_maps_only_to_touch(self) -> None:
        current = frame()
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate(
            key="inspect:p-new",
            kind="inspect_object",
            priority=0.95,
            target_ref="t1_7",
            target_signature="p-new",
        )
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "manipulate")
        self.assertEqual(action.parameters, {"verb": "touch", "effector": "hand_right"})
        self.assertEqual(action.target_ref, "t1_7")

    def test_inspect_uses_other_hand_when_right_hand_is_occupied(self) -> None:
        current = frame(right_occupied=1.0)
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate(
            key="inspect:p-new",
            kind="inspect_object",
            priority=0.95,
            target_ref="t1_7",
            target_signature="p-new",
        )
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.parameters["effector"], "hand_left")

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

    def test_scan_direction_uses_scan_attempt_not_observation_parity(self) -> None:
        memory = WorkingMemory()
        first_frame = frame(sequence=2)
        memory.add(first_frame)
        first = ExplorationPolicy().choose(
            first_frame,
            GoalCandidate(
                "scan:obstacle",
                "scan_obstacle",
                0.8,
                reason={"scan_attempt": 1},
            ),
            memory,
        )
        second_frame = frame(sequence=3)
        second = ExplorationPolicy().choose(
            second_frame,
            GoalCandidate(
                "scan:obstacle",
                "scan_obstacle",
                0.8,
                reason={"scan_attempt": 2},
            ),
            memory,
        )
        third = ExplorationPolicy().choose(
            second_frame,
            GoalCandidate(
                "scan:obstacle",
                "scan_obstacle",
                0.8,
                reason={"scan_attempt": 3},
            ),
            memory,
        )
        self.assertGreater(first.parameters["yaw_delta_rad"], 0)
        self.assertGreater(second.parameters["yaw_delta_rad"], 0)
        self.assertLess(third.parameters["yaw_delta_rad"], 0)

    def test_explore_bypasses_near_central_obstacle(self) -> None:
        current = frame(sequence=7, blocked=True)
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate(
            "explore:open",
            "explore",
            0.5,
            reason={"explore_attempt": 1},
        )
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "move")
        self.assertNotEqual(action.parameters["strafe"], 0.0)
        self.assertLess(action.parameters["forward"], 1.0)
        self.assertEqual(action.rationale["policy"], "cautious_obstacle_bypass")

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
