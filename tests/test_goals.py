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
