from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from alua.cognition import CognitiveCore
from alua.memory import WorkingMemory
from alua.perception import build_frame
from alua.store import Store
from alua.topology import PerceptualTopology
from alua.world_model import EgocentricWorldModel


def frame(sequence: int):
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {
            "vision": {"rays": [{
                "appearance_id": "p-new",
                "distance_fraction": 0.1,
                "blocks_motion": False,
                "target_ref": f"t{sequence}",
            }]},
            "vitals": {
                "health_fraction": 1.0,
                "stamina_fraction": 0.9,
                "hunger_signal": 0.1,
                "thirst_signal": 0.1,
                "fatigue_signal": 0.1,
                "breath_fraction": 1.0,
            },
        },
    })


class CognitionTests(unittest.TestCase):
    def test_snapshot_persists_explainable_cognitive_state(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "a.sqlite3")
            try:
                memory = WorkingMemory()
                world = EgocentricWorldModel()
                topology = PerceptualTopology()
                core = CognitiveCore()
                current = frame(1)
                memory.add(current)
                world.update(current, {"p-new"})
                topology.observe(store, "alua:1", current)
                snapshot = core.observe(
                    frame=current,
                    novel_appearance_ids={"p-new"},
                    memory=memory,
                    world_model=world,
                    topology=topology,
                    store=store,
                    agent_id="alua:1",
                    session_id="s1",
                )
                self.assertTrue(snapshot.context_signature.startswith("place-"))
                self.assertGreaterEqual(snapshot.attention.salience, 0.5)
                self.assertTrue(snapshot.missions)
                record = store.cognitive_record(
                    "alua:1",
                    "cognition:last-state",
                )
                self.assertIsNotNone(record)
                self.assertEqual(
                    record["record_kind"],
                    "metacognitive_state",
                )
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
