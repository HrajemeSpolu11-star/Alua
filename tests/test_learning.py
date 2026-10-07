from __future__ import annotations

import unittest

from alua.learning import motor_quality, motor_success


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


if __name__ == "__main__":
    unittest.main()
