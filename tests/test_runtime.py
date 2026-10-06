from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from alua.config import Config
from alua.runtime import Runtime
from alua.store import Store


class FakeBridge:
    def __init__(self):
        self.actions = []
        self.action_sequence = 0

    def session(self):
        return {
            "schema_version": 1,
            "agent_id": "alua:1",
            "session_id": "world-1",
            "last_observation_sequence": 2,
            "last_action_sequence": self.action_sequence,
        }

    def observations(self, after_sequence: int):
        if after_sequence == 0:
            return [{
                "schema_version": 1,
                "agent_id": "alua:1",
                "sequence": 1,
                "simulation_time": 0.25,
                "channels": {
                    "vision": {
                        "rays": [{
                            "appearance_id": "pabc",
                            "distance_fraction": 0.05,
                            "blocks_motion": True,
                            "liquid": False,
                            "target_ref": "t1_7",
                        }]
                    },
                    "contact": {"damage_signal": 0},
                },
            }]
        if after_sequence == 1:
            return [{
                "schema_version": 1,
                "agent_id": "alua:1",
                "sequence": 2,
                "simulation_time": 0.50,
                "channels": {
                    "vision": {"rays": [{"distance_fraction": 1.0, "empty": True}]},
                    "contact": {"damage_signal": 0},
                    "motor": {
                        "events": [{
                            "source_sequence": 1,
                            "success_signal": 1,
                            "feedback_signal": "effect",
                            "effort_signal": 0.03,
                            "age_fraction": 0.0,
                        }]
                    },
                },
            }]
        return []

    def submit_action(self, action):
        self.actions.append(action)
        self.action_sequence += 1
        return {
            "request_id": f"a_{self.action_sequence}",
            "action_sequence": self.action_sequence,
            "status": "queued",
            "duplicate": False,
        }


class RuntimeTests(unittest.TestCase):
    def test_touch_outcome_becomes_evidence_based_belief(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = Config(
                agent_id="alua:1",
                bridge_url="http://127.0.0.1:8787",
                agent_token="a" * 48,
                database_path=Path(tmp) / "alua.sqlite3",
            )
            store = Store(config.database_path)
            bridge = FakeBridge()
            try:
                runtime = Runtime(config, store, bridge)
                first = runtime.step()
                self.assertEqual(first.observations_processed, 1)
                self.assertTrue(first.action_submitted)
                self.assertEqual(bridge.actions[0]["type"], "manipulate")
                self.assertEqual(bridge.actions[0]["parameters"], {"verb": "touch"})
                self.assertEqual(bridge.actions[0]["target_ref"], "t1_7")
                self.assertEqual(store.summary("alua:1")["pending_expectations"], 1)

                second = runtime.step()
                self.assertEqual(second.outcomes_resolved, 1)
                belief = store.belief("alua:1", "appearance:pabc:touch:effect")
                self.assertIsNotNone(belief)
                self.assertGreater(belief["confidence"], 0.5)

                decision = store.decision(first.decision_id)
                self.assertNotIn("t1_7", decision["action_json"])
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
