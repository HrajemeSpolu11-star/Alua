from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from alua.perception import build_frame
from alua.store import Store


def observation(sequence: int, target: str = "t1_1") -> dict:
    return {
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {
            "vision": {
                "rays": [{
                    "appearance_id": "p123",
                    "distance_fraction": 0.5,
                    "target_ref": target,
                }]
            }
        },
    }


class StoreTests(unittest.TestCase):
    def test_session_reset_preserves_learning_but_resets_cursor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "alua.sqlite3"
            store = Store(path)
            try:
                self.assertTrue(store.apply_session("alua:1", "s1"))
                frame = build_frame(observation(1))
                store.record_observation("alua:1", "s1", frame)
                self.assertEqual(store.summary("alua:1")["known_appearance_signatures"], 1)
                self.assertTrue(store.apply_session("alua:1", "s2"))
                state = store.state("alua:1")
                self.assertEqual(state["last_observation_sequence"], 0)
                self.assertEqual(store.summary("alua:1")["known_appearance_signatures"], 1)
            finally:
                store.close()

    def test_persistent_episode_does_not_store_target_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "alua.sqlite3"
            store = Store(path)
            try:
                store.apply_session("alua:1", "s1")
                store.record_observation("alua:1", "s1", build_frame(observation(1, "t1_secret")))
            finally:
                store.close()
            db = sqlite3.connect(path)
            try:
                payload = db.execute("SELECT percept_json FROM episodes").fetchone()[0]
            finally:
                db.close()
            self.assertNotIn("t1_secret", payload)
            self.assertIn("p123", payload)

    def test_persistent_decision_strips_target_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "alua.sqlite3"
            store = Store(path)
            try:
                store.apply_session("alua:1", "s1")
                store.record_decision(
                    "mind-x",
                    "alua:1",
                    "s1",
                    1,
                    {
                        "schema_version": 1,
                        "agent_id": "alua:1",
                        "client_action_id": "mind-x",
                        "type": "manipulate",
                        "target_ref": "t1_secret",
                        "parameters": {"verb": "touch"},
                    },
                    {"target_ref": "t1_secret"},
                )
            finally:
                store.close()
            db = sqlite3.connect(path)
            try:
                action_json, rationale_json = db.execute(
                    "SELECT action_json,rationale_json FROM decisions WHERE decision_id='mind-x'"
                ).fetchone()
            finally:
                db.close()
            self.assertNotIn("t1_secret", action_json)
            self.assertNotIn("target_ref", action_json)
            self.assertNotIn("t1_secret", rationale_json)


if __name__ == "__main__":
    unittest.main()
