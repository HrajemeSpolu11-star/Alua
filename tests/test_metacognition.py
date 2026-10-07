from __future__ import annotations

import unittest

from alua.metacognition import Metacognition


class MetacognitionTests(unittest.TestCase):
    def test_low_progress_revisit_loop_requests_backtrack(self) -> None:
        meta = Metacognition()
        for index in range(12):
            meta.observe_place("place-a" if index % 2 == 0 else "place-b")
            meta.record_action({
                "type": "move",
                "parameters": {"mode": "walk"},
            })
            meta.record_outcome(progress=0.05, prediction_error=0.7)
        state = meta.assess(
            sensory_uncertainty=0.4,
            topology_revisit_ratio=0.8,
            dead_end_score=0.7,
        )
        self.assertGreater(state.stagnation, 0.6)
        self.assertEqual(state.recommended_mode, "backtrack")
        self.assertIn("dead_end_evidence", state.reasons)


if __name__ == "__main__":
    unittest.main()
