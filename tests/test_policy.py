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


    def test_critical_breath_surfaces_with_swim_action(self) -> None:
        current = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 20,
            "simulation_time": 20.0,
            "channels": {
                "vitals": {"breath_fraction": 0.2, "stamina_fraction": 0.8},
                "locomotion": {"head_submerged_signal": 1, "feet_in_liquid_signal": 1},
            },
        })
        memory = WorkingMemory()
        memory.add(current)
        action = ExplorationPolicy().choose(
            current,
            GoalCandidate("survive:breath", "survive_breath", 1.25),
            memory,
        )
        self.assertEqual(action.action_type, "move")
        self.assertEqual(action.parameters["mode"], "swim")
        self.assertGreater(action.parameters["vertical"], 0)

    def test_step_affordance_uses_vault_not_blind_strafe(self) -> None:
        current = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 21,
            "simulation_time": 21.0,
            "channels": {
                "vision": {"rays": [{
                    "distance_fraction": 0.06,
                    "appearance_id": "p-step",
                    "blocks_motion": True,
                }]},
                "vitals": {
                    "stamina_fraction": 0.8,
                    "fatigue_signal": 0.1,
                    "breath_fraction": 1.0,
                },
                "locomotion": {
                    "grounded_signal": 1,
                    "step_up_signal": 1,
                    "front_head_blocked_signal": 0,
                    "overhead_blocked_signal": 0,
                    "gap_ahead_signal": 0,
                },
            },
        })
        memory = WorkingMemory()
        memory.add(current)
        action = ExplorationPolicy().terrain_intent(
            current,
            GoalCandidate("explore:open", "explore", 0.5),
            memory,
        )
        self.assertIsNotNone(action)
        self.assertEqual(action.parameters["mode"], "vault")

    def test_unvaultable_wall_does_not_get_a_vault_command(self) -> None:
        for kind, signals, stamina in (
            ("high_wall", {"step_up_signal": 0., "front_head_blocked_signal": 1.}, .8),
            ("ceiling", {"step_up_signal": 1., "overhead_blocked_signal": 1.}, .8),
            ("low_stamina", {"step_up_signal": 1.}, .05),
            ("not_grounded", {"step_up_signal": 1., "grounded_signal": 0.}, .8),
        ):
            with self.subTest(case=kind):
                movement = {"grounded_signal": 1., "step_up_signal": 1.,
                            "front_head_blocked_signal": 0.,
                            "overhead_blocked_signal": 0., **signals}
                current = build_frame({
                    "schema_version": 1, "sequence": 30, "simulation_time": 30.,
                    "channels": {
                        "vision": {"rays": [
                            {"distance_fraction": .06, "blocks_motion": True},
                        ]},
                        "vitals": {"stamina_fraction": stamina},
                        "locomotion": movement,
                    },
                })
                mem = WorkingMemory()
                mem.add(current)
                action = ExplorationPolicy().terrain_intent(
                    current, GoalCandidate("explore:open", "explore", .5), mem,
                )
                self.assertNotEqual(action.parameters.get("mode") if action else None,
                                    "vault")

    def test_verified_gap_landing_enables_jump(self) -> None:
        current = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 22,
            "simulation_time": 22.0,
            "channels": {
                "vision": {"rays": [{"distance_fraction": 1.0, "empty": True}]},
                "vitals": {
                    "stamina_fraction": 0.8,
                    "fatigue_signal": 0.1,
                    "breath_fraction": 1.0,
                },
                "locomotion": {
                    "grounded_signal": 1,
                    "gap_ahead_signal": 1,
                    "jump_gap_signal": 1,
                    "safe_drop_signal": 0,
                },
            },
        })
        memory = WorkingMemory()
        memory.add(current)
        action = ExplorationPolicy().terrain_intent(
            current,
            GoalCandidate("explore:open", "explore", 0.5),
            memory,
        )
        self.assertEqual(action.parameters["mode"], "jump")

    def test_unknown_unsafe_drop_is_not_walked_into(self) -> None:
        current = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 23,
            "simulation_time": 23.0,
            "channels": {
                "vision": {"rays": [{"distance_fraction": 1.0, "empty": True}]},
                "vitals": {"stamina_fraction": 0.8, "fatigue_signal": 0.1},
                "locomotion": {
                    "grounded_signal": 1,
                    "gap_ahead_signal": 1,
                    "jump_gap_signal": 0,
                    "safe_drop_signal": 0,
                },
            },
        })
        memory = WorkingMemory()
        memory.add(current)
        action = ExplorationPolicy().terrain_intent(
            current,
            GoalCandidate("explore:open", "explore", 0.5),
            memory,
        )
        self.assertEqual(action.parameters["forward"], 0.0)
        self.assertNotEqual(action.parameters["strafe"], 0.0)

    def test_hunger_consumes_selected_inventory_slot(self) -> None:
        current = frame(sequence=24)
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate(
            "need:consume:pfood",
            "satisfy_hunger",
            0.9,
            target_signature="pfood",
            reason={"phase": "consume_inventory", "slot_index": 3},
        )
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "interact")
        self.assertEqual(action.parameters, {"verb": "consume", "slot_index": 3})

    def test_collect_uses_pickup_to_inventory(self) -> None:
        current = frame(sequence=25)
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate(
            "collect:p-new",
            "collect_object",
            0.8,
            target_ref="t25_1",
            target_signature="p-new",
        )
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "manipulate")
        self.assertEqual(action.parameters["verb"], "pickup")
        self.assertTrue(action.parameters["store"])

    def test_mining_exists_only_for_explicit_need_goal(self) -> None:
        current = frame(sequence=26)
        memory = WorkingMemory()
        memory.add(current)
        goal = GoalCandidate(
            "need:mine:p-resource",
            "acquire_required_resource",
            0.9,
            target_ref="t26_1",
            target_signature="p-resource",
            reason={"phase": "mine_required"},
        )
        action = ExplorationPolicy().choose(current, goal, memory)
        self.assertEqual(action.action_type, "manipulate")
        self.assertEqual(action.parameters["verb"], "break_object")
        self.assertEqual(action.rationale["policy"], "need_driven_mining")


if __name__ == "__main__":
    unittest.main()
