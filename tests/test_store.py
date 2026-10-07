from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from alua.perception import build_frame
from alua.store import SCHEMA_VERSION, Store


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

    def test_persistent_decision_and_expectation_strip_target_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "alua.sqlite3"
            store = Store(path)
            action = {
                "schema_version": 1,
                "agent_id": "alua:1",
                "client_action_id": "mind-x",
                "type": "manipulate",
                "target_ref": "t1_secret",
                "parameters": {"verb": "touch"},
            }
            try:
                store.apply_session("alua:1", "s1")
                store.record_decision("mind-x", "alua:1", "s1", 1, action, {"target_ref": "t1_secret"})
                store.mark_decision_submitted("mind-x", "req", "queued", 9)
                store.record_expectation(
                    decision_id="mind-x",
                    agent_id="alua:1",
                    session_id="s1",
                    bridge_action_sequence=9,
                    action_type="manipulate",
                    target_signature="p123",
                    action=action,
                    created_sequence=1,
                )
            finally:
                store.close()
            db = sqlite3.connect(path)
            try:
                action_json, rationale_json = db.execute(
                    "SELECT action_json,rationale_json FROM decisions WHERE decision_id='mind-x'"
                ).fetchone()
                expectation_json = db.execute(
                    "SELECT action_json FROM expectations WHERE decision_id='mind-x'"
                ).fetchone()[0]
            finally:
                db.close()
            for payload in (action_json, rationale_json, expectation_json):
                self.assertNotIn("t1_secret", payload)
                self.assertNotIn("target_ref", payload)

    def test_expectation_resolution_updates_belief(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            try:
                store.apply_session("alua:1", "s1")
                action = {
                    "schema_version": 1,
                    "agent_id": "alua:1",
                    "client_action_id": "mind-x",
                    "type": "move",
                    "parameters": {"forward": 1},
                }
                store.record_decision("mind-x", "alua:1", "s1", 1, action, {})
                store.mark_decision_submitted("mind-x", "req", "queued", 3)
                store.record_expectation(
                    decision_id="mind-x",
                    agent_id="alua:1",
                    session_id="s1",
                    bridge_action_sequence=3,
                    action_type="move",
                    target_signature=None,
                    action=action,
                    created_sequence=1,
                )
                expectation = store.resolve_expectation(
                    agent_id="alua:1",
                    session_id="s1",
                    bridge_action_sequence=3,
                    outcome={"success_signal": 1, "feedback_signal": "effect"},
                    resolved_sequence=2,
                )
                self.assertIsNotNone(expectation)
                belief = store.update_binary_belief(
                    agent_id="alua:1",
                    belief_key="action:move:motor_effect",
                    kind="procedural",
                    subject_signature="move",
                    relation="motor_effect",
                    value={"expected": True},
                    supported=True,
                    sequence=2,
                )
                self.assertGreater(belief["confidence"], 0.5)
            finally:
                store.close()

    def test_session_change_invalidates_pending_expectation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            try:
                store.apply_session("alua:1", "s1")
                action = {
                    "schema_version": 1,
                    "agent_id": "alua:1",
                    "client_action_id": "mind-x",
                    "type": "move",
                    "parameters": {"forward": 1},
                }
                store.record_decision("mind-x", "alua:1", "s1", 1, action, {})
                store.mark_decision_submitted("mind-x", "req", "queued", 4)
                store.record_expectation(
                    decision_id="mind-x",
                    agent_id="alua:1",
                    session_id="s1",
                    bridge_action_sequence=4,
                    action_type="move",
                    target_signature=None,
                    action=action,
                    created_sequence=1,
                )
                store.apply_session("alua:1", "s2")
                self.assertEqual(store.pending_expectation_count("alua:1", "s1"), 0)
                self.assertEqual(store.decision("mind-x")["status"], "invalidated_session")
            finally:
                store.close()

    def test_latest_submitted_goal_is_scoped_to_current_session(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            try:
                store.apply_session("alua:1", "old-session")
                action = {
                    "schema_version": 1,
                    "agent_id": "alua:1",
                    "client_action_id": "mind-old",
                    "type": "look",
                    "parameters": {"yaw_delta_rad": 0.45, "pitch_delta_rad": 0.0},
                }
                store.record_decision(
                    "mind-old",
                    "alua:1",
                    "old-session",
                    500,
                    action,
                    {},
                    goal_key="scan:recovery",
                    goal_kind="scan_recovery",
                )
                store.mark_decision_submitted("mind-old", "req-old", "queued", 77)

                store.apply_session("alua:1", "new-session")
                self.assertIsNone(
                    store.latest_submitted_goal("alua:1", "new-session")
                )

                action2 = {
                    "schema_version": 1,
                    "agent_id": "alua:1",
                    "client_action_id": "mind-new",
                    "type": "move",
                    "parameters": {"forward": 1.0, "strafe": 0.0},
                }
                store.record_decision(
                    "mind-new",
                    "alua:1",
                    "new-session",
                    1,
                    action2,
                    {},
                    goal_key="explore:open",
                    goal_kind="explore",
                )
                store.mark_decision_submitted("mind-new", "req-new", "queued", 1)
                latest = store.latest_submitted_goal("alua:1", "new-session")
                self.assertIsNotNone(latest)
                self.assertEqual(latest["goal_kind"], "explore")
                self.assertEqual(latest["bridge_action_sequence"], 1)
            finally:
                store.close()

    def test_v1_database_is_backed_up_and_migrated(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.sqlite3"
            db = sqlite3.connect(path)
            db.executescript(
                """
                CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                INSERT INTO meta(key,value) VALUES('schema_version','1');
                CREATE TABLE decisions(
                    decision_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    observation_sequence INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    action_json TEXT NOT NULL,
                    rationale_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_id TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                """
            )
            db.commit()
            db.close()

            store = Store(path)
            try:
                self.assertIsNotNone(store.last_backup_path)
                self.assertTrue(store.last_backup_path.exists())
                self.assertEqual(store.summary("alua:1")["schema_version"], SCHEMA_VERSION)
            finally:
                store.close()


    def test_goal_outcomes_and_schema_v3_tables(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            try:
                attempted = store.record_goal_attempt(
                    agent_id="alua:1",
                    goal_key="explore:open",
                    kind="explore",
                    subject_signature=None,
                    priority=0.5,
                    sequence=1,
                )
                self.assertEqual(attempted["attempts"], 1)
                completed = store.record_goal_outcome(
                    agent_id="alua:1",
                    goal_key="explore:open",
                    kind="explore",
                    subject_signature=None,
                    supported=False,
                    sequence=2,
                )
                self.assertEqual(completed["failures"], 1)
                self.assertEqual(store.summary("alua:1")["schema_version"], 3)
                self.assertEqual(store.summary("alua:1")["goals"], 1)
            finally:
                store.close()

    def test_v2_database_is_backed_up_and_migrated_to_v3(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy-v2.sqlite3"
            db = sqlite3.connect(path)
            db.executescript(
                """
                CREATE TABLE meta(key TEXT PRIMARY KEY,value TEXT NOT NULL);
                INSERT INTO meta(key,value) VALUES('schema_version','2');
                CREATE TABLE decisions(
                    decision_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    observation_sequence INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    action_json TEXT NOT NULL,
                    rationale_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_id TEXT,
                    bridge_action_sequence INTEGER,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                """
            )
            db.commit()
            db.close()

            store = Store(path)
            try:
                self.assertIsNotNone(store.last_backup_path)
                self.assertTrue(store.last_backup_path.exists())
                summary = store.summary("alua:1")
                self.assertEqual(summary["schema_version"], 3)
                self.assertIn("skills", summary)
                self.assertIn("goals", summary)
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
