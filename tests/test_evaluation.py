from __future__ import annotations

import unittest

from alua.evaluation import evaluate_trace


class EvaluationTests(unittest.TestCase):
    def test_detects_look_loop_and_reports_outcomes(self) -> None:
        trace = [
            {
                "action_type": "look",
                "goal_kind": "scan_obstacle",
                "status": "resolved",
                "expectation_state": "resolved",
                "outcome_success": True,
            },
            {
                "action_type": "look",
                "goal_kind": "scan_periodic",
                "status": "resolved",
                "expectation_state": "resolved",
                "outcome_success": True,
            },
            {
                "action_type": "move",
                "goal_kind": "explore",
                "status": "resolved",
                "expectation_state": "resolved",
                "outcome_success": False,
            },
        ]
        metrics = evaluate_trace(trace)
        self.assertTrue(metrics["quality_flags"]["look_loop_detected"])
        self.assertEqual(metrics["longest_look_streak"], 2)
        self.assertEqual(metrics["resolved_outcomes"], 3)
        self.assertEqual(metrics["resolved_moves"], 1)
        self.assertEqual(metrics["move_success_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
