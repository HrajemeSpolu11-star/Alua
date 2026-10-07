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


if __name__ == "__main__":
    unittest.main()
