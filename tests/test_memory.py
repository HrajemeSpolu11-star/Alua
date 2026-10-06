from __future__ import annotations

import unittest

from alua.memory import WorkingMemory
from alua.perception import build_frame


def frame(sequence: int, damage: float = 0.0):
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {"contact": {"damage_signal": damage}},
    })


class WorkingMemoryTests(unittest.TestCase):
    def test_is_bounded_and_tracks_damage(self) -> None:
        memory = WorkingMemory(capacity=4)
        for sequence in range(1, 7):
            memory.add(frame(sequence, 0.6 if sequence == 6 else 0.0))
        self.assertEqual(memory.recent_sequences(), (3, 4, 5, 6))
        self.assertEqual(memory.recent_damage_signal(), 0.6)

    def test_clear_drops_ephemeral_context(self) -> None:
        memory = WorkingMemory(capacity=4)
        memory.add(frame(1))
        memory.clear()
        self.assertEqual(len(memory), 0)


if __name__ == "__main__":
    unittest.main()
