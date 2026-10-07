from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from alua.object_memory import ObjectMemory
from alua.perception import build_frame
from alua.store import Store


def frame(sequence: int, appearance: str = "p1"):
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {
            "vision": {"rays": [{
                "appearance_id": appearance,
                "distance_fraction": 0.3,
                "blocks_motion": False,
            }]}
        },
    })


class ObjectMemoryTests(unittest.TestCase):
    def test_object_persists_after_leaving_view(self) -> None:
        memory = ObjectMemory()
        memory.observe(frame(1))
        empty = build_frame({
            "schema_version": 1,
            "agent_id": "alua:1",
            "sequence": 2,
            "simulation_time": 2.0,
            "channels": {"vision": {"rays": []}},
        })
        memory.observe(empty)
        self.assertIsNotNone(memory.track("p1"))
        self.assertGreater(memory.track("p1").persistence_confidence, 0.2)

    def test_object_concept_is_persisted_without_target_ref(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "a.sqlite3")
            try:
                memory = ObjectMemory()
                memory.observe(frame(1), store=store, agent_id="alua:1")
                record = store.cognitive_record("alua:1", "object:p1")
                self.assertIsNotNone(record)
                self.assertEqual(record["record_kind"], "object_concept")
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
