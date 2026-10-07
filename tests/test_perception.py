from __future__ import annotations

import json
import unittest

from alua.perception import build_frame


class PerceptionTests(unittest.TestCase):
    def test_body_schema_remains_available_to_policy_without_world_truth(self) -> None:
        frame = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 1,
            "simulation_time": 0.25,
            "channels": {
                "body_schema": {
                    "schema_version": 1,
                    "effectors": {
                        "hand_right": {"present_signal": 1, "touch_signal": 1, "occupied_signal": 0}
                    },
                }
            },
        })
        hand = frame.persistent["channels"]["body_schema"]["effectors"]["hand_right"]
        self.assertEqual(hand["touch_signal"], 1)

    def test_target_ref_is_ephemeral_but_keeps_runtime_association(self) -> None:
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
                        "blocks_motion": True,
                        "liquid": False,
                        "target_ref": "t3_9",
                    }]
                }
            },
        })
        self.assertEqual(frame.target_refs, ("t3_9",))
        self.assertEqual(frame.appearance_ids, ("p123",))
        self.assertEqual(frame.targets[0].appearance_id, "p123")
        self.assertEqual(frame.targets[0].distance_fraction, 0.2)
        self.assertNotIn("t3_9", json.dumps(frame.persistent))

    def test_visual_percept_survives_without_target_ref(self) -> None:
        frame = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 5,
            "simulation_time": 2.5,
            "channels": {
                "vision": {
                    "rays": [{
                        "appearance_id": "p-expired",
                        "distance_fraction": 0.06,
                        "blocks_motion": True,
                        "liquid": False,
                    }]
                }
            },
        })
        self.assertEqual(frame.target_refs, ())
        self.assertEqual(len(frame.targets), 1)
        self.assertIsNone(frame.targets[0].target_ref)
        self.assertEqual(frame.targets[0].appearance_id, "p-expired")
        self.assertTrue(frame.targets[0].blocks_motion)

    def test_motor_feedback_is_extracted(self) -> None:
        frame = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 4,
            "simulation_time": 2.0,
            "channels": {
                "motor": {
                    "events": [{
                        "source_sequence": 7,
                        "success_signal": 0.72,
                        "progress_signal": 0.72,
                        "slip_signal": 0.15,
                        "feedback_signal": "effect",
                        "effort_signal": 0.2,
                        "age_fraction": 0.1,
                    }]
                }
            },
        })
        self.assertEqual(frame.motor_events[0]["source_sequence"], 7)
        self.assertEqual(frame.motor_events[0]["feedback_signal"], "effect")
        self.assertEqual(frame.motor_events[0]["progress_signal"], 0.72)
        self.assertEqual(frame.motor_events[0]["slip_signal"], 0.15)


if __name__ == "__main__":
    unittest.main()
