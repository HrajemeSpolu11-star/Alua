from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from alua.perception import build_frame
from alua.store import Store
from alua.topology import PerceptualTopology, perceptual_place_signature


def frame(sequence: int, front: float = 0.8, appearance: str = "p1"):
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {
            "vision": {
                "rays": [
                    {
                        "appearance_id": appearance,
                        "distance_fraction": front,
                        "blocks_motion": front < 0.2,
                        "liquid": False,
                    },
                    {"distance_fraction": 1.0, "empty": True},
                    {"distance_fraction": 0.7, "empty": True},
                ]
            },
            "contact": {"supported": True, "feet_in_liquid": False},
        },
    })


class TopologyTests(unittest.TestCase):
    def test_signature_has_no_target_ref_or_absolute_position_dependency(self) -> None:
        first = frame(1)
        second = frame(99)
        self.assertEqual(
            perceptual_place_signature(first),
            perceptual_place_signature(second),
        )

    def test_failed_transition_creates_persistent_navigation_penalty(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            topology = PerceptualTopology()
            try:
                origin = frame(1, front=0.9, appearance="p-origin")
                topology.observe(store, "alua:1", origin)
                action = {
                    "type": "move",
                    "parameters": {"forward": 0.18, "strafe": -0.78},
                }
                for sequence in range(2, 5):
                    topology.begin_action(action)
                    topology.finish_action(
                        store,
                        "alua:1",
                        action,
                        False,
                        frame(sequence, front=0.9, appearance="p-origin"),
                    )
                penalties = topology.persistent_penalties(store, "alua:1")
                self.assertGreater(penalties.get("left", 0.0), 0.0)
                self.assertEqual(penalties.get("right", 0.0), 0.0)
            finally:
                store.close()

    def test_successful_transition_is_remembered_across_topology_instance(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "alua.sqlite3")
            try:
                first = PerceptualTopology()
                origin = frame(1, appearance="p-origin")
                first.observe(store, "alua:1", origin)
                action = {
                    "type": "move",
                    "parameters": {"forward": 1.0, "strafe": 0.0},
                }
                first.begin_action(action)
                first.finish_action(
                    store,
                    "alua:1",
                    action,
                    True,
                    frame(2, appearance="p-destination"),
                )

                second = PerceptualTopology()
                second.observe(store, "alua:1", origin)
                stats = store.perceptual_transition_stats(
                    "alua:1",
                    second.current_signature,
                    "forward",
                )
                self.assertEqual(stats["successes"], 1)
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
