from __future__ import annotations

import unittest

from alua.errors import ProtocolError
from alua.schema import validate_observation, validate_session


class SchemaTests(unittest.TestCase):
    def test_nested_world_truth_is_rejected(self) -> None:
        with self.assertRaises(ProtocolError):
            validate_observation({
                "schema_version": 1,
                "agent_id": "alua:1",
                "sequence": 1,
                "simulation_time": 0.1,
                "channels": {"vision": {"rays": [{"material": "wood"}]}},
            }, "alua:1")

    def test_session_must_match_agent(self) -> None:
        with self.assertRaises(ProtocolError):
            validate_session({
                "schema_version": 1,
                "agent_id": "alua:2",
                "session_id": "s1",
                "last_observation_sequence": 0,
                "last_action_sequence": 0,
            }, "alua:1")


if __name__ == "__main__":
    unittest.main()
