from __future__ import annotations

import json
import unittest

from alua.perception import build_frame


class PerceptionTests(unittest.TestCase):
    def test_target_ref_is_ephemeral(self) -> None:
        frame = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 3,
            "simulation_time": 1.5,
            "channels": {
                "vision": {
                    "rays": [{
                        "appearance_id": "p123",
                        "distance_fraction": 0.2,
                        "target_ref": "t3_9",
                    }]
                }
            },
        })
        self.assertEqual(frame.target_refs, ("t3_9",))
        self.assertEqual(frame.appearance_ids, ("p123",))
        self.assertNotIn("t3_9", json.dumps(frame.persistent))


if __name__ == "__main__":
    unittest.main()
