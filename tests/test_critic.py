from __future__ import annotations

import unittest

from alua.critic import BehaviorCritic


class CriticTests(unittest.TestCase):
    def test_repeated_look_is_detected(self) -> None:
        critic = BehaviorCritic()
        critic.record_submission("look", "scan_obstacle", 1)
        first = critic.assess()
        self.assertTrue(first.suppress_scan)
        self.assertFalse(first.force_replan)

        critic.record_submission("look", "scan_periodic", 2)
        second = critic.assess()
        self.assertTrue(second.force_replan)
        self.assertIn("repeated_look", second.reasons)

    def test_three_failed_moves_force_replan(self) -> None:
        critic = BehaviorCritic()
        action = {"type": "move", "parameters": {"forward": 1.0, "strafe": 0.0}}
        for _ in range(3):
            critic.record_outcome(action, False)
        result = critic.assess()
        self.assertTrue(result.force_replan)
        self.assertIn("three_failed_moves", result.reasons)


if __name__ == "__main__":
    unittest.main()
