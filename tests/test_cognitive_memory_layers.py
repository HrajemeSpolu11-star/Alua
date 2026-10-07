from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from alua.concepts import ConceptLearner
from alua.perception import build_frame
from alua.scene import SceneIntegrator
from alua.social import SocialCognition
from alua.store import Store
from alua.temporal import TemporalModel


def make_frame(sequence: int, simulation_time: float):
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": simulation_time,
        "channels": {
            "vision": {"rays": [{
                "appearance_id": "p1",
                "distance_fraction": 0.3,
                "blocks_motion": False,
            }]},
            "hearing": {"events": [{
                "signature_id": "sound-a",
                "intensity": 0.4,
            }]},
            "contact": {
                "supported": True,
                "feet_in_liquid": False,
                "head_submerged": False,
            },
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


class CognitiveMemoryLayerTests(unittest.TestCase):
    def test_scene_and_temporal_recurrence_are_bounded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "a.sqlite3")
            try:
                temporal = TemporalModel()
                scene1 = SceneIntegrator.integrate(make_frame(1, 10.0))
                scene2 = SceneIntegrator.integrate(make_frame(2, 15.0))
                self.assertEqual(scene1.signature, scene2.signature)
                temporal.observe(
                    store,
                    agent_id="alua:1",
                    signature=scene1.signature,
                    simulation_time=10.0,
                    sequence=1,
                )
                pattern = temporal.observe(
                    store,
                    agent_id="alua:1",
                    signature=scene2.signature,
                    simulation_time=15.0,
                    sequence=2,
                )
                self.assertEqual(pattern.occurrences, 2)
                self.assertAlmostEqual(pattern.mean_interval, 5.0)
            finally:
                store.close()

    def test_concept_formation_uses_shared_empirical_relations(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "a.sqlite3")
            try:
                for appearance in ("p-a", "p-b"):
                    for relation in ("touch_effect", "pickup_effect"):
                        store.update_binary_belief(
                            agent_id="alua:1",
                            belief_key=f"appearance:{appearance}:{relation}",
                            kind="empirical",
                            subject_signature=appearance,
                            relation=relation,
                            value={"expected": True},
                            supported=True,
                            sequence=1,
                        )
                        store.update_binary_belief(
                            agent_id="alua:1",
                            belief_key=f"appearance:{appearance}:{relation}",
                            kind="empirical",
                            subject_signature=appearance,
                            relation=relation,
                            value={"expected": True},
                            supported=True,
                            sequence=2,
                        )
                concepts = ConceptLearner().consolidate(
                    store,
                    agent_id="alua:1",
                    sequence=3,
                )
                self.assertTrue(concepts)
                self.assertEqual(set(concepts[0].members), {"p-a", "p-b"})
            finally:
                store.close()

    def test_social_layer_is_inert_without_explicit_channel(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / "a.sqlite3")
            try:
                social = SocialCognition()
                entities = social.observe(
                    make_frame(1, 1.0),
                    store,
                    agent_id="alua:1",
                )
                self.assertEqual(entities, ())
                self.assertEqual(
                    len(
                        store.cognitive_records(
                            "alua:1",
                            record_kind="social_model",
                        )
                    ),
                    0,
                )
            finally:
                store.close()


if __name__ == "__main__":
    unittest.main()
