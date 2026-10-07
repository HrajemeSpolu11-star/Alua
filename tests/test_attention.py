from __future__ import annotations

import unittest

from alua.attention import AttentionSystem
from alua.perception import build_frame


def observation(sequence: int, appearance: str, distance: float) -> dict:
    return {
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {
            "vision": {"rays": [{
                "appearance_id": appearance,
                "distance_fraction": distance,
                "blocks_motion": True,
            }]}
        },
    }


class AttentionTests(unittest.TestCase):
    def test_novel_close_target_gets_focus(self) -> None:
        system = AttentionSystem()
        frame = build_frame(observation(1, "p-new", 0.08))
        state = system.assess(frame, {"p-new"})
        self.assertEqual(state.focus_signature, "p-new")
        self.assertGreater(state.salience, 0.5)

    def test_change_creates_surprise(self) -> None:
        system = AttentionSystem()
        system.assess(build_frame(observation(1, "p-a", 0.5)), set())
        state = system.assess(build_frame(observation(2, "p-b", 0.2)), set())
        self.assertGreater(state.surprise, 0.0)


if __name__ == "__main__":
    unittest.main()
