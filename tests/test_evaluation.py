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


    def test_long_successful_travel_is_not_false_stereotype(self) -> None:
        trace = [
            {
                "action_type": "move",
                "goal_kind": "explore",
                "status": "resolved",
                "expectation_state": "resolved",
                "outcome_success": True,
                "progress_signal": 0.90,
            }
            for _ in range(10)
        ]
        metrics = evaluate_trace(trace)
        self.assertEqual(metrics["longest_move_streak"], 10)
        self.assertFalse(metrics["quality_flags"]["action_stereotype_detected"])
        self.assertFalse(metrics["quality_flags"]["navigation_stagnation_detected"])

    def test_low_progress_move_loop_is_detected(self) -> None:
        trace = [
            {
                "action_type": "move",
                "goal_kind": "explore",
                "status": "resolved",
                "expectation_state": "resolved",
                "outcome_success": False,
                "progress_signal": 0.30,
            }
            for _ in range(8)
        ]
        metrics = evaluate_trace(trace)
        self.assertTrue(metrics["quality_flags"]["action_stereotype_detected"])
        self.assertTrue(metrics["quality_flags"]["navigation_stagnation_detected"])
        self.assertLess(metrics["mean_move_progress"], 0.55)

    def test_real_field_backtrack_loop_rejected_even_at_99_percent_motor_success(self) -> None:
        # Android field evidence: 496 of 500 goals were spatial_backtrack;
        # 495 successful physical moves did NOT represent exploration.
        trace = [
            {
                "action_type": "move",
                "goal_kind": "spatial_backtrack" if i < 496 else "satisfy_thirst",
                "status": "resolved",
                "expectation_state": "resolved",
                "outcome_success": i % 125 != 0,
                "progress_signal": 0.78,
            }
            for i in range(500)
        ]
        result = evaluate_trace(trace)
        self.assertGreater(result["move_success_rate"], 0.98)
        self.assertEqual(result["longest_backtrack_streak"], 496)
        self.assertEqual(result["spatial_backtrack_fraction"], 0.992)
        self.assertTrue(result["quality_flags"]["spatial_backtrack_dominance_detected"])
        self.assertFalse(acceptance_report(result)["passed"])
        self.assertFalse(acceptance_report(result)["checks"]["no_spatial_backtrack_dominance"])

    def test_short_verified_backtrack_is_not_marked_as_infinite_loop(self) -> None:
        trace = [
            {
                "action_type": "move",
                "goal_kind": "spatial_backtrack",
                "status": "resolved",
                "expectation_state": "resolved",
                "outcome_success": True,
                "progress_signal": .92,
            }
            for _ in range(7)
        ]
        trace.extend({
            "action_type": "move",
            "goal_kind": "explore",
            "status": "resolved",
            "expectation_state": "resolved",
            "outcome_success": True,
            "progress_signal": .92,
        } for _ in range(70))
        result = evaluate_trace(trace)
        self.assertFalse(result["quality_flags"]["spatial_backtrack_dominance_detected"])
        self.assertTrue(acceptance_report(result)["passed"])

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
