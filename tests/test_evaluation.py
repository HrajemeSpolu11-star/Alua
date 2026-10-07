from __future__ import annotations

import unittest

from alua.evaluation import acceptance_report, evaluate_sensory_replay, evaluate_trace


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


    def test_sensory_replay_and_acceptance_gate(self) -> None:
        episodes = [
            {
                "schema_version": 1,
                "sequence": 1,
                "simulation_time": 1.0,
                "channels": {
                    "vision": {"rays": [{"distance_fraction": 1.0, "empty": True}]}
                },
            },
            {
                "schema_version": 1,
                "sequence": 2,
                "simulation_time": 2.0,
                "channels": {
                    "vision": {"rays": [{"distance_fraction": 0.8, "empty": True}]}
                },
            },
        ]
        sensory = evaluate_sensory_replay(episodes)
        self.assertEqual(sensory["observations"], 2)
        self.assertGreaterEqual(sensory["unique_perceptual_places"], 1)

        behavior = evaluate_trace([
            {
                "action_type": "move",
                "goal_kind": "explore",
                "status": "resolved",
                "expectation_state": "resolved",
                "outcome_success": True,
            }
        ])
        report = acceptance_report(behavior, sensory)
        self.assertTrue(report["passed"])


if __name__ == "__main__":
    unittest.main()
