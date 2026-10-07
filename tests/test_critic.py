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

    def test_three_low_progress_moves_force_replan(self) -> None:
        critic = BehaviorCritic()
        action = {"type": "move", "parameters": {"forward": 1.0, "strafe": 0.0}}
        for sequence in range(1, 4):
            critic.record_submission("move", "explore", sequence, maneuver="forward")
            critic.record_outcome(action, False, quality=0.25)
        result = critic.assess()
        self.assertTrue(result.force_replan)
        self.assertIn("poor_move_progress", result.reasons)

    def test_repeated_successful_forward_travel_is_not_a_stereotype(self) -> None:
        critic = BehaviorCritic()
        action = {"type": "move", "parameters": {"forward": 1.0, "strafe": 0.0}}
        for sequence in range(1, 10):
            critic.record_submission("move", "explore", sequence, maneuver="forward")
            critic.record_outcome(action, True, quality=0.92)
        result = critic.assess()
        self.assertFalse(result.force_replan)
        self.assertNotIn("maneuver_stereotype", result.reasons)


if __name__ == "__main__":
    unittest.main()
