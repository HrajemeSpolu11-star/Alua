from __future__ import annotations

import unittest

from alua.memory import WorkingMemory
from alua.perception import build_frame
from alua.policy import ExplorationPolicy


def make_frame(sequence: int, *, distance: float | None = None, appearance: str = "p1", damage: float = 0.0):
    ray = {"distance_fraction": 1.0, "empty": True}
    if distance is not None:
        ray = {
            "distance_fraction": distance,
            "appearance_id": appearance,
            "blocks_motion": True,
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


class PolicyTests(unittest.TestCase):
    def test_novel_close_target_is_touched_not_destroyed(self) -> None:
        frame = make_frame(1, distance=0.05, appearance="p-new")
        memory = WorkingMemory()
        memory.add(frame)
        action = ExplorationPolicy().choose(frame, {"p-new"}, memory)
        self.assertEqual(action.action_type, "manipulate")
        self.assertEqual(action.parameters, {"verb": "touch"})
        self.assertEqual(action.target_signature, "p-new")
        self.assertTrue(action.target_ref)

    def test_close_obstacle_causes_scan(self) -> None:
        frame = make_frame(2, distance=0.10)
        memory = WorkingMemory()
        memory.add(frame)
        action = ExplorationPolicy().choose(frame, set(), memory)
        self.assertEqual(action.action_type, "look")

    def test_clear_space_causes_cautious_move(self) -> None:
        frame = make_frame(3)
        memory = WorkingMemory()
        memory.add(frame)
        action = ExplorationPolicy().choose(frame, set(), memory)
        self.assertEqual(action.action_type, "move")
        self.assertLess(action.parameters["speed_fraction"], 1)

    def test_damage_has_priority(self) -> None:
        frame = make_frame(4, damage=0.5)
        memory = WorkingMemory()
        memory.add(frame)
        action = ExplorationPolicy().choose(frame, set(), memory)
        self.assertEqual(action.action_type, "move")
        self.assertLess(action.parameters["forward"], 0)


if __name__ == "__main__":
    unittest.main()
