from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from alua.learning import learn_from_motor_outcome, motor_quality, motor_success
from alua.store import Store


class LearningTests(unittest.TestCase):
    def test_partial_effect_is_not_motor_success(self) -> None:
        event = {
            "success_signal": 0.38,
            "progress_signal": 0.38,
            "feedback_signal": "partial_effect",
        }
        self.assertAlmostEqual(motor_quality(event), 0.38)
        self.assertFalse(motor_success(event))

    def test_directional_progress_above_threshold_is_success(self) -> None:
        event = {
            "success_signal": 0.72,
            "progress_signal": 0.72,
            "feedback_signal": "effect",
        }
        self.assertTrue(motor_success(event))

    def test_resistance_cannot_be_success_even_with_bad_signal(self) -> None:
        event = {
            "success_signal": 0.9,
            "progress_signal": 0.9,
            "feedback_signal": "resistance",
        }
        self.assertFalse(motor_success(event))

    def test_consumption_learns_nutrition_from_body_effect_not_item_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            try:
                expectation = {
                    "decision_id": "d1",
                    "session_id": "s1",
                    "action_type": "interact",
                    "target_signature": "pfood",
                    "action": {
                        "type": "interact",
                        "parameters": {"verb": "consume", "slot_index": 2},
                    },
                }
                learn_from_motor_outcome(
                    store,
                    "alua:1",
                    expectation,
                    {
                        "success_signal": 1.0,
                        "progress_signal": 1.0,
                        "feedback_signal": "effect",
                        "nutrition_delta_signal": 0.12,
                        "hydration_delta_signal": 0.01,
                    },
                    8,
                )
                belief = store.belief(
                    "alua:1",
                    "appearance:pfood:consume:nutrition_effect",
                )
                self.assertIsNotNone(belief)
                self.assertEqual(belief["support_count"], 1)
                self.assertEqual(belief["contradiction_count"], 0)
            finally:
                store.close()

    def test_non_food_consumption_records_contradicting_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            try:
                expectation = {
                    "decision_id": "d2",
                    "session_id": "s1",
                    "action_type": "interact",
                    "target_signature": "pstone",
                    "action": {
                        "type": "interact",
                        "parameters": {"verb": "consume", "slot_index": 1},
                    },
                }
                learn_from_motor_outcome(
                    store,
                    "alua:1",
                    expectation,
                    {
                        "success_signal": 0.0,
                        "progress_signal": 0.0,
                        "feedback_signal": "no_effect",
                        "nutrition_delta_signal": 0.0,
                    },
                    9,
                )
                belief = store.belief(
                    "alua:1",
                    "appearance:pstone:consume:nutrition_effect",
                )
                self.assertIsNotNone(belief)
                self.assertEqual(belief["support_count"], 0)
                self.assertEqual(belief["contradiction_count"], 1)
            finally:
                store.close()

    def test_drinking_learns_hydration_effect(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            try:
                expectation = {
                    "decision_id": "d3",
                    "session_id": "s1",
                    "action_type": "manipulate",
                    "target_signature": "pwater",
                    "action": {
                        "type": "manipulate",
                        "parameters": {"verb": "drink"},
                    },
                }
                learn_from_motor_outcome(
                    store,
                    "alua:1",
                    expectation,
                    {
                        "success_signal": 1.0,
                        "progress_signal": 1.0,
                        "feedback_signal": "effect",
                        "hydration_delta_signal": 0.2,
                    },
                    10,
                )
                belief = store.belief(
                    "alua:1",
                    "appearance:pwater:drink:hydration_effect",
                )
                self.assertIsNotNone(belief)
                self.assertEqual(belief["support_count"], 1)
            finally:
                store.close()

    def test_jump_outcome_is_learned_as_locomotion_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            try:
                expectation = {
                    "decision_id": "d4",
                    "session_id": "s1",
                    "action_type": "move",
                    "target_signature": None,
                    "action": {
                        "type": "move",
                        "parameters": {
                            "mode": "jump",
                            "forward": 1.0,
                            "strafe": 0.0,
                        },
                    },
                }
                learn_from_motor_outcome(
                    store,
                    "alua:1",
                    expectation,
                    {
                        "success_signal": 0.8,
                        "progress_signal": 0.8,
                        "feedback_signal": "effect",
                    },
                    11,
                )
                belief = store.belief("alua:1", "locomotion:jump:motor_effect")
                self.assertIsNotNone(belief)
                self.assertEqual(belief["support_count"], 1)
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
