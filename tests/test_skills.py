from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from alua.goals import GoalCandidate
from alua.skills import SkillLibrary
from alua.store import Store


class SkillLibraryTests(unittest.TestCase):
    def test_skill_is_promoted_only_after_repeated_verified_success(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            library = SkillLibrary()
            expectation = {
                "goal_kind": "explore",
                "target_signature": None,
                "action": {
                    "type": "move",
                    "parameters": {
                        "forward": 1.0,
                        "strafe": 0.0,
                        "duration_s": 0.30,
                        "speed_fraction": 0.55,
                    },
                },
            }
            try:
                first = library.learn(store, "alua:1", expectation, supported=True, sequence=1)
                second = library.learn(store, "alua:1", expectation, supported=True, sequence=2)
                self.assertFalse(first["reusable"])
                self.assertFalse(second["reusable"])

                third = library.learn(store, "alua:1", expectation, supported=True, sequence=3)
                self.assertTrue(third["reusable"])
                self.assertGreaterEqual(third["confidence"], 0.70)

                retrieved = library.retrieve(
                    store,
                    "alua:1",
                    GoalCandidate("explore:open", "explore", 0.5),
                )
                self.assertIsNotNone(retrieved)
                skill_key, intent = retrieved
                self.assertEqual(skill_key, third["skill_key"])
                self.assertEqual(intent.action_type, "move")
            finally:
                store.close()

    def test_failures_can_demote_a_previously_reusable_skill(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            library = SkillLibrary()
            expectation = {
                "goal_kind": "scan_obstacle",
                "target_signature": None,
                "action": {
                    "type": "look",
                    "parameters": {"yaw_delta_rad": 0.45, "pitch_delta_rad": 0.0},
                },
            }
            try:
                record = None
                for sequence in range(1, 4):
                    record = library.learn(store, "alua:1", expectation, supported=True, sequence=sequence)
                self.assertTrue(record["reusable"])
                for sequence in range(4, 7):
                    record = library.learn(store, "alua:1", expectation, supported=False, sequence=sequence)
                self.assertFalse(record["reusable"])
            finally:
                store.close()

    def test_persisted_skill_never_contains_target_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "alua.sqlite3"
            store = Store(path)
            try:
                store.update_skill_evidence(
                    agent_id="alua:1",
                    skill_key="skill-test",
                    kind="manipulate",
                    goal_kind="inspect_object",
                    target_signature="p123",
                    steps=[{
                        "type": "manipulate",
                        "target_ref": "t-secret",
                        "parameters": {"verb": "touch", "target_ref": "t-nested"},
                    }],
                    supported=True,
                    sequence=1,
                    min_successes=3,
                    min_confidence=0.70,
                )
            finally:
                store.close()
            db = sqlite3.connect(path)
            try:
                payload = db.execute(
                    "SELECT steps_json FROM skills WHERE skill_key='skill-test'"
                ).fetchone()[0]
            finally:
                db.close()
            self.assertNotIn("target_ref", payload)
            self.assertNotIn("t-secret", payload)
            self.assertNotIn("t-nested", payload)


if __name__ == "__main__":
    unittest.main()
