from __future__ import annotations

import unittest

from alua.perception import build_frame
from alua.world_model import EgocentricWorldModel


def frame(sequence: int = 1):
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {
            "vision": {
                "rays": [
                    {
                        "appearance_id": "p-front",
                        "distance_fraction": 0.08,
                        "blocks_motion": True,
                    },
                    {
                        "appearance_id": "p-left-new",
                        "distance_fraction": 0.90,
                        "blocks_motion": False,
                    },
                    {
                        "appearance_id": "p-right",
                        "distance_fraction": 0.30,
                        "blocks_motion": False,
                    },
                    {"distance_fraction": 1.0, "empty": True},
                    {"distance_fraction": 1.0, "empty": True},
                ]
            }
        },
    })


class WorldModelTests(unittest.TestCase):
    def test_builds_egocentric_frontier_without_absolute_position(self) -> None:
        model = EgocentricWorldModel()
        model.update(frame(), {"p-left-new"})

        self.assertTrue(model.front_is_blocked())
        self.assertEqual(model.most_promising_horizontal_sector(), "left")
        summary = model.diagnostic_summary()
        self.assertNotIn("position", summary)
        self.assertGreater(summary["scores"]["left"], summary["scores"]["right"])

    def test_reset_removes_session_local_evidence(self) -> None:
        model = EgocentricWorldModel()
        model.update(frame(), {"p-left-new"})
        self.assertGreater(model.sectors["front"].confidence, 0)
        model.reset()
        self.assertEqual(model.sequence, 0)
        self.assertEqual(model.sectors["front"].samples, 0)


if __name__ == "__main__":
    unittest.main()
