from __future__ import annotations

import unittest

from alua.goals import IntrinsicCurriculum, ReflexGoalSelector
from alua.memory import WorkingMemory
from alua.perception import build_frame


def make_frame(
    sequence: int,
    *,
    distance: float | None = None,
    appearance: str = "p1",
    damage: float = 0.0,
    blocks_motion: bool = True,
):
    ray = {"distance_fraction": 1.0, "empty": True}
    if distance is not None:
        ray = {
            "distance_fraction": distance,
            "appearance_id": appearance,
            "blocks_motion": blocks_motion,
            "liquid": False,
            "target_ref": f"t{sequence}_1",
        }
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {
            "vision": {"rays": [ray]},
            "contact": {"damage_signal": damage},
        },
    })


class GoalTests(unittest.TestCase):
    def test_reflex_preempts_ordinary_curriculum(self) -> None:
        frame = make_frame(1, distance=0.05, appearance="p-new", damage=0.4)
        memory = WorkingMemory()
        memory.add(frame)
        goal = ReflexGoalSelector().choose(frame, memory)
        self.assertIsNotNone(goal)
        self.assertEqual(goal.kind, "survive_damage")
        self.assertEqual(goal.priority, 1.0)

    def test_novel_reachable_target_becomes_intrinsic_goal(self) -> None:
        frame = make_frame(1, distance=0.05, appearance="p-new")
        memory = WorkingMemory()
        memory.add(frame)
        goal = IntrinsicCurriculum().choose(
            frame,
            {"p-new"},
            memory,
            lambda _: None,
        )
        self.assertEqual(goal.kind, "inspect_object")
        self.assertEqual(goal.target_signature, "p-new")
        self.assertTrue(goal.target_ref)

    def test_known_object_is_rechecked_only_while_uncertain(self) -> None:
        frame = make_frame(2, distance=0.05, appearance="p-known")
        memory = WorkingMemory()
        memory.add(frame)

        goal = IntrinsicCurriculum().choose(
            frame,
            set(),
            memory,
            lambda key: {"attempts": 1, "successes": 1, "failures": 0} if key == "inspect:p-known" else None,
        )
        self.assertEqual(goal.kind, "inspect_object")

        finished = IntrinsicCurriculum().choose(
            frame,
            set(),
            memory,
            lambda key: {"attempts": 3, "successes": 3, "failures": 0} if key == "inspect:p-known" else None,
        )
        self.assertNotEqual(finished.kind, "inspect_object")

    def test_obstacle_scan_requires_intervening_exploration(self) -> None:
        current = make_frame(11, distance=0.10, appearance="p-wall")
        memory = WorkingMemory()
        memory.add(current)

        initial = IntrinsicCurriculum().choose(
            current,
            set(),
            memory,
            lambda _: None,
        )
        self.assertEqual(initial.kind, "scan_obstacle")

        def after_scan(key: str):
            if key == "scan:obstacle":
                return {"attempts": 1, "successes": 1, "failures": 0, "last_sequence": 11}
            return None

        followup = IntrinsicCurriculum().choose(
            make_frame(12, distance=0.10, appearance="p-wall"),
            set(),
            memory,
            after_scan,
            previous_goal_kind="scan_obstacle",
        )
        self.assertEqual(followup.kind, "explore")

        def after_move(key: str):
            if key == "scan:obstacle":
                return {"attempts": 1, "successes": 1, "failures": 0, "last_sequence": 11}
            if key == "explore:open":
                return {"attempts": 1, "successes": 0, "failures": 1, "last_sequence": 13}
            return None

        rescan = IntrinsicCurriculum().choose(
            make_frame(14, distance=0.10, appearance="p-wall"),
            set(),
            memory,
            after_move,
            previous_goal_kind="explore",
        )
        self.assertEqual(rescan.kind, "scan_obstacle")

    def test_recovery_scan_does_not_starve_followup_exploration(self) -> None:
        current = make_frame(21)
        memory = WorkingMemory()
        memory.add(current)

        def failed_explore(key: str):
            if key == "explore:open":
                return {
                    "attempts": 4,
                    "successes": 1,
                    "failures": 3,
                    "last_sequence": 20,
                }
            return None

        recovery = IntrinsicCurriculum().choose(current, set(), memory, failed_explore)
        self.assertEqual(recovery.kind, "scan_recovery")

        def after_recovery(key: str):
            if key == "explore:open":
                return {
                    "attempts": 4,
                    "successes": 1,
                    "failures": 3,
                    "last_sequence": 20,
                }
            if key == "scan:recovery":
                return {
                    "attempts": 1,
                    "successes": 1,
                    "failures": 0,
                    "last_sequence": 21,
                }
            return None

        next_goal = IntrinsicCurriculum().choose(
            make_frame(22),
            set(),
            memory,
            after_recovery,
            previous_goal_kind="scan_recovery",
        )
        self.assertEqual(next_goal.kind, "explore")

    def test_different_scan_kinds_cannot_chain_back_to_back(self) -> None:
        frame = make_frame(25, distance=0.10, appearance="p-wall")
        memory = WorkingMemory()
        memory.add(frame)

        def stats(key: str):
            if key == "explore:open":
                return {
                    "attempts": 4,
                    "successes": 1,
                    "failures": 3,
                    "last_sequence": 24,
                }
            return None

        # Bez globální brány by zde obstacle/recovery/periodic kandidáti
        # mohli po jiném scanu znovu vyprodukovat další look.
        goal = IntrinsicCurriculum().choose(
            frame,
            set(),
            memory,
            stats,
            previous_goal_kind="scan_periodic",
        )
        self.assertEqual(goal.kind, "explore")

    def test_any_previous_look_blocks_immediate_scan_chain(self) -> None:
        frame = make_frame(26, distance=0.10, appearance="p-wall")
        memory = WorkingMemory()
        memory.add(frame)

        def stats(key: str):
            if key == "explore:open":
                return {
                    "attempts": 4,
                    "successes": 1,
                    "failures": 3,
                    "last_sequence": 25,
                }
            return None

        goal = IntrinsicCurriculum().choose(
            frame,
            set(),
            memory,
            stats,
            previous_goal_kind="explore",
            previous_action_type="look",
            information_need=0.95,
        )
        self.assertEqual(goal.kind, "explore")

    def test_information_scan_is_driven_by_model_uncertainty(self) -> None:
        frame = make_frame(6)
        memory = WorkingMemory()
        memory.add(frame)

        uncertain = IntrinsicCurriculum().choose(
            frame,
            set(),
            memory,
            lambda _: None,
            information_need=0.90,
        )
        self.assertEqual(uncertain.kind, "scan_periodic")
        self.assertEqual(uncertain.reason["trigger"], "model_uncertainty")

        known = IntrinsicCurriculum().choose(
            frame,
            set(),
            memory,
            lambda _: None,
            information_need=0.10,
        )
        self.assertEqual(known.kind, "explore")

    def test_zero_distance_is_really_nearest(self) -> None:
        frame = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 30,
            "simulation_time": 30.0,
            "channels": {
                "vision": {
                    "rays": [
                        {
                            "distance_fraction": 0.0,
                            "appearance_id": "p-touching",
                            "blocks_motion": True,
                            "target_ref": "t30_1",
                        },
                        {
                            "distance_fraction": 0.04,
                            "appearance_id": "p-near",
                            "blocks_motion": True,
                            "target_ref": "t30_2",
                        },
                    ]
                },
                "contact": {"damage_signal": 0},
            },
        })
        memory = WorkingMemory()
        memory.add(frame)
        goal = IntrinsicCurriculum().choose(
            frame,
            {"p-touching", "p-near"},
            memory,
            lambda _: None,
        )
        self.assertEqual(goal.target_signature, "p-touching")

    def test_old_failures_do_not_force_recovery_after_successes_dominate(self) -> None:
        frame = make_frame(41)
        memory = WorkingMemory()
        memory.add(frame)

        def stats(key: str):
            if key == "explore:open":
                return {
                    "attempts": 8,
                    "successes": 5,
                    "failures": 3,
                    "last_sequence": 40,
                }
            return None

        goal = IntrinsicCurriculum().choose(frame, set(), memory, stats)
        self.assertEqual(goal.kind, "explore")

    def test_repeated_failed_exploration_promotes_recovery_scan(self) -> None:
        frame = make_frame(3)
        memory = WorkingMemory()
        memory.add(frame)

        def stats(key: str):
            if key == "explore:open":
                return {"attempts": 4, "successes": 1, "failures": 3}
            return None

        goal = IntrinsicCurriculum().choose(frame, set(), memory, stats)
        self.assertEqual(goal.kind, "scan_recovery")
        self.assertGreater(goal.priority, 0.5)


    def test_low_breath_underwater_preempts_damage_free_state(self) -> None:
        current = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 50,
            "simulation_time": 50.0,
            "channels": {
                "contact": {"damage_signal": 0},
                "vitals": {"breath_fraction": 0.2},
                "locomotion": {"head_submerged_signal": 1},
            },
        })
        memory = WorkingMemory()
        memory.add(current)
        goal = ReflexGoalSelector().choose(current, memory)
        self.assertIsNotNone(goal)
        self.assertEqual(goal.kind, "survive_breath")

    def test_thirst_approaches_visible_liquid_before_drinking(self) -> None:
        current = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 51,
            "simulation_time": 51.0,
            "channels": {
                "vitals": {
                    "thirst_signal": 0.8,
                    "hunger_signal": 0.0,
                    "stamina_fraction": 0.8,
                    "fatigue_signal": 0.1,
                    "breath_fraction": 1.0,
                },
                "vision": {"rays": [{
                    "distance_fraction": 0.4,
                    "appearance_id": "p-liquid",
                    "blocks_motion": False,
                    "liquid": True,
                    "target_ref": "t51_1",
                }]},
            },
        })
        memory = WorkingMemory()
        memory.add(current)
        goal = IntrinsicCurriculum().choose(
            current,
            set(),
            memory,
            lambda _: None,
            information_need=0.0,
        )
        self.assertEqual(goal.kind, "satisfy_thirst")
        self.assertEqual(goal.reason["phase"], "approach")
        self.assertEqual(goal.target_signature, "p-liquid")

    def test_hunger_uses_inventory_experiment_before_world_mining(self) -> None:
        current = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 52,
            "simulation_time": 52.0,
            "channels": {
                "vitals": {
                    "hunger_signal": 0.8,
                    "thirst_signal": 0.0,
                    "stamina_fraction": 0.8,
                    "fatigue_signal": 0.1,
                    "breath_fraction": 1.0,
                },
                "inventory": {
                    "load_fraction": 0.1,
                    "slots": [{
                        "slot_index": 4,
                        "appearance_id": "p-unknown",
                        "count": 1,
                        "mass_fraction": 0.03,
                    }],
                },
                "vision": {"rays": [{"distance_fraction": 1.0, "empty": True}]},
            },
        })
        memory = WorkingMemory()
        memory.add(current)
        goal = IntrinsicCurriculum().choose(
            current,
            set(),
            memory,
            lambda _: None,
            information_need=0.0,
        )
        self.assertEqual(goal.kind, "satisfy_hunger")
        self.assertEqual(goal.reason["phase"], "consume_inventory")
        self.assertEqual(goal.reason["slot_index"], 4)

    def test_collect_follows_completed_inspection_phase(self) -> None:
        current = make_frame(53, distance=0.05, appearance="p-object", blocks_motion=False)
        memory = WorkingMemory()
        memory.add(current)

        def inspected_stats(key: str):
            if key == "inspect:p-object":
                return {"attempts": 3, "successes": 3, "failures": 0}
            return None

        goal = IntrinsicCurriculum().choose(
            current,
            set(),
            memory,
            inspected_stats,
            information_need=0.0,
        )
        self.assertEqual(goal.kind, "collect_object")
        self.assertEqual(goal.target_signature, "p-object")

    def test_mining_requires_need_and_failed_pickup_evidence(self) -> None:
        current = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 54,
            "simulation_time": 54.0,
            "channels": {
                "vitals": {
                    "hunger_signal": 0.9,
                    "thirst_signal": 0.0,
                    "stamina_fraction": 0.8,
                    "fatigue_signal": 0.1,
                    "breath_fraction": 1.0,
                },
                "inventory": {"load_fraction": 0.0, "slots": []},
                "vision": {"rays": [{
                    "distance_fraction": 0.05,
                    "appearance_id": "p-food",
                    "blocks_motion": True,
                    "liquid": False,
                    "target_ref": "t54_1",
                }]},
            },
        })
        memory = WorkingMemory()
        memory.add(current)

        def stats(key: str):
            if key == "need:pickup:p-food":
                return {"attempts": 2, "successes": 0, "failures": 2}
            return None

        def belief(key: str):
            if key == "appearance:p-food:consume:nutrition_effect":
                return {"support_count": 2, "contradiction_count": 0}
            return None

        goal = IntrinsicCurriculum().choose(
            current,
            set(),
            memory,
            stats,
            information_need=0.0,
            belief_lookup=belief,
        )
        self.assertEqual(goal.kind, "acquire_required_resource")
        self.assertEqual(goal.reason["phase"], "mine_required")


if __name__ == "__main__":
    unittest.main()
