from __future__ import annotations

import io
import json
import os
from pathlib import Path
import tempfile
import unittest

from alua.flight_recorder import output_lines, secure_log_file, snapshot


class StoreFixture:
    def __init__(self):
        self.decision_status = "queued"
    def state(self, agent_id):
        return {"session_id": "sim-a"}
    def session_episodes(self, agent_id, session_id, *, limit):
        return [{"sequence": 5, "appearance_ids": ["p1234"],
                 "sensor": {"vision": {"rays": []}}}]
    def session_trace(self, agent_id, session_id, *, limit):
        return [{"decision_id": "d1", "session_id": "sim-a",
                 "observation_sequence": 5, "goal_key": "explore:open",
                 "goal_kind": "explore", "skill_key": None,
                 "status": self.decision_status, "action": {"type": "move"},
                 "rationale": {"policy": "walk", "cognitive_state": {
                     "metacognition": {"stagnation": 0.2},
                     "route_depth": 4}},
                 "bridge_action_sequence": 14,
                 "expectation_state": "resolved" if self.decision_status == "done" else "pending",
                 "outcome": {"source_sequence": 14, "progress_signal": 0.7}
                     if self.decision_status == "done" else None,
                 "outcome_success": True if self.decision_status == "done" else None,
                 "progress_signal": 0.7 if self.decision_status == "done" else None}]
    def cognitive_record(self, agent_id, key):
        return {"payload": {"meta": {"loop_risk": 0.1}}, "updated_at": 123.4}


class FlightRecorderTests(unittest.TestCase):
    def test_reports_real_stored_sensory_and_decision_rationale(self):
        rows = snapshot(StoreFixture(), "alua:1", 25, True)
        self.assertEqual([r["event"] for r in rows],
                         ["sensory_episode", "cognitive_decision",
                          "cognitive_model_snapshot"])
        self.assertEqual(rows[1]["cognitive_state"]["route_depth"], 4)
        self.assertEqual(rows[1]["bridge_action_sequence"], 14)
        self.assertEqual(rows[1]["verified_motor_outcome"], None)

    def test_one_shot_jsonl_and_expected_outcome_do_not_become_fake_success(self):
        fixture = StoreFixture()
        buf = io.StringIO()
        output_lines(fixture, "alua:1", 10, True, buf)
        lines = [json.loads(s) for s in buf.getvalue().splitlines()]
        assert lines[1]["outcome_success"] is None
        fixture.decision_status = "done"
        buf2 = io.StringIO()
        output_lines(fixture, "alua:1", 10, False, buf2)
        rows = [json.loads(s) for s in buf2.getvalue().splitlines()]
        self.assertEqual(rows[0]["verified_motor_outcome"]["source_sequence"], 14)
        self.assertEqual(rows[0]["outcome_success"], True)

    def test_private_append_only_file(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "operator" / "mind.jsonl")
            with secure_log_file(path) as stream:
                stream.write('{"first":true}\n')
            with secure_log_file(path) as stream:
                stream.write('{"second":true}\n')
            content = Path(path).read_text()
            self.assertIn('"first"', content)
            self.assertIn('"second"', content)
            if os.name == "posix":
                self.assertEqual(os.stat(path).st_mode & 0o777, 0o600)


if __name__ == "__main__":
    unittest.main()
