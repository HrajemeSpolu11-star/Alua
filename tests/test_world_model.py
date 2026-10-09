from __future__ import annotations

import unittest

from alua.perception import build_frame
from alua.world_model import EgocentricWorldModel
from alua.spatial_memory import SpatialMemory


def frame(sequence: int = 1):
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {
            "vision": {
                "rays": [
                    {
                        "appearance_id": "p-front",
                        "distance_fraction": 0.08,
                        "blocks_motion": True,
                    },
                    {
                        "appearance_id": "p-left-new",
                        "distance_fraction": 0.90,
                        "blocks_motion": False,
                    },
                    {
                        "appearance_id": "p-right",
                        "distance_fraction": 0.30,
                        "blocks_motion": False,
                    },
                    {"distance_fraction": 1.0, "empty": True},
                    {"distance_fraction": 1.0, "empty": True},
                ]
            }
        },
    })


class WorldModelTests(unittest.TestCase):
    def test_builds_egocentric_frontier_without_absolute_position(self) -> None:
        model = EgocentricWorldModel()
        model.update(frame(), {"p-left-new"})

        self.assertTrue(model.front_is_blocked())
        self.assertEqual(model.most_promising_horizontal_sector(), "left")
        summary = model.diagnostic_summary()
        self.assertNotIn("position", summary)
        self.assertGreater(summary["scores"]["left"], summary["scores"]["right"])

    def test_physical_one_node_step_is_traversable_not_dead_end(self) -> None:
        # Vision still collides with stone: only the body's *own current*
        # locomotion sensing and stamina can reinterpret it as a step.
        blocked_rays = [
            {"appearance_id": "p-front", "distance_fraction": .06, "blocks_motion": True},
            {"appearance_id": "p-left", "distance_fraction": .06, "blocks_motion": True},
            {"appearance_id": "p-right", "distance_fraction": .06, "blocks_motion": True},
        ]
        step_frame = build_frame({
            "schema_version": 1, "sequence": 2, "simulation_time": 2.,
            "channels": {
                "vision": {"rays": blocked_rays},
                "locomotion": {
                    "grounded_signal": 1., "step_up_signal": 1.,
                    "front_head_blocked_signal": 0.,
                    "overhead_blocked_signal": 0.,
                },
                "vitals": {"stamina_fraction": .8},
            },
        })
        model = EgocentricWorldModel()
        model.update(step_frame)
        self.assertTrue(model.front_step_traversable())
        self.assertFalse(model.front_is_blocked())
        self.assertFalse(SpatialMemory._dead_end_from_model(model))
        self.assertGreater(model.sector_score("front"), 0.5)
        self.assertTrue(model.diagnostic_summary()["front_step_traversable"])

        # One-block collision remains real; the route is "traversable with
        # vault", NOT a claim that the node is empty.
        self.assertGreater(model.sectors["front"].blocked_probability, .9)

    def test_high_wall_overhead_low_stamina_and_missing_probes_still_block(self) -> None:
        # The same front wall must remain blocked in all non-vaultable cases.
        def sensed(seq: int, *, step: float, head: float,
                   overhead: float, stamina: float, grounded: float = 1.) -> object:
            return build_frame({
                "schema_version": 1, "sequence": seq,
                "simulation_time": float(seq),
                "channels": {
                    "vision": {"rays": [
                        {"distance_fraction": .06, "blocks_motion": True,
                         "appearance_id": "p-front"},
                    ]},
                    "locomotion": {
                        "grounded_signal": grounded,
                        "step_up_signal": step,
                        "front_head_blocked_signal": head,
                        "overhead_blocked_signal": overhead,
                    },
                    "vitals": {"stamina_fraction": stamina},
                },
            })
        model = EgocentricWorldModel()
        model.update(sensed(1, step=1, head=0, overhead=0, stamina=.8))
        self.assertFalse(model.front_is_blocked())
        for seq, kwargs in enumerate((
            dict(step=0, head=1, overhead=0, stamina=.8),
            dict(step=1, head=1, overhead=0, stamina=.8),
            dict(step=1, head=0, overhead=1, stamina=.8),
            dict(step=1, head=0, overhead=0, stamina=.05),
            dict(step=1, head=0, overhead=0, stamina=.8, grounded=0),
        ), start=2):
            model.update(sensed(seq, **kwargs))
            self.assertFalse(model.front_step_traversable())
            self.assertTrue(model.front_is_blocked())
        model.update(frame(10))  # no locomotion; old step evidence expires
        self.assertTrue(model.front_is_blocked())
        model.invalidate_view()
        self.assertFalse(model.front_step_traversable())

    def test_view_invalidation_prevents_mixing_rotated_egocentric_sectors(self) -> None:
        model = EgocentricWorldModel()
        model.update(frame(), {"p-left-new"})
        self.assertGreater(model.sectors["left"].confidence, 0)
        model.invalidate_view()
        for evidence in model.sectors.values():
            self.assertEqual(evidence.samples, 0)
            self.assertEqual(evidence.confidence, 0.0)

    def test_reset_removes_session_local_evidence(self) -> None:
        model = EgocentricWorldModel()
        model.update(frame(), {"p-left-new"})
        self.assertGreater(model.sectors["front"].confidence, 0)
        model.reset()
        self.assertEqual(model.sequence, 0)
        self.assertEqual(model.sectors["front"].samples, 0)


if __name__ == "__main__":
    unittest.main()
