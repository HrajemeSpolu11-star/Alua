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

    def session(self):
        return {
            "schema_version": 1,
            "agent_id": "alua:1",
            "session_id": "world-1",
            "last_observation_sequence": 1,
            "last_action_sequence": 0,
        }

    def observations(self, after_sequence: int):
        if after_sequence >= 1:
            return []
        return [{
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 1,
            "simulation_time": 0.25,
            "channels": {
                "vision": {
                    "rays": [{
                        "appearance_id": "pabc",
                        "distance_fraction": 0.4,
                        "target_ref": "t1_7",
                    }]
                }
            },
        }]

    def submit_action(self, action):
        self.actions.append(action)
        return {
            "request_id": "a_test",
            "action_sequence": 1,
            "status": "queued",
            "duplicate": False,
        }


class RuntimeTests(unittest.TestCase):
    def test_one_cycle_persists_perception_and_submits_safe_action(self) -> None:
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
                result = runtime.step()
                self.assertEqual(result.observations_processed, 1)
                self.assertTrue(result.action_submitted)
                self.assertEqual(bridge.actions[0]["type"], "wait")
                self.assertEqual(bridge.actions[0]["duration"], 0.25)
                self.assertNotIn("target_ref", bridge.actions[0])
                summary = store.summary("alua:1")
                self.assertEqual(summary["episodes"], 1)
                self.assertEqual(summary["known_appearance_signatures"], 1)

                second = runtime.step()
                self.assertEqual(second.observations_processed, 0)
                self.assertFalse(second.action_submitted)
                self.assertEqual(len(bridge.actions), 1)
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
