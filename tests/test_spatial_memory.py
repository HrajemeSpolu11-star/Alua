from __future__ import annotations

import unittest

from alua.perception import build_frame
from alua.spatial_memory import SpatialMemory
from alua.world_model import EgocentricWorldModel


def frame(sequence: int, appearance: str, blocked: bool = False):
    rays = []
    for idx, name in enumerate((appearance, appearance + "-l", appearance + "-r")):
        rays.append({
            "appearance_id": name,
            "distance_fraction": 0.05 if blocked else 0.8,
            "blocks_motion": blocked,
        })
    return build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": sequence,
        "simulation_time": float(sequence),
        "channels": {"vision": {"rays": rays}},
    })


class SpatialMemoryTests(unittest.TestCase):
    def test_dead_end_backtracks_along_remembered_route(self) -> None:
        spatial = SpatialMemory()
        model = EgocentricWorldModel()

        first = frame(1, "a", blocked=False)
        spatial.observe(first)
        model.update(first)
        action = {
            "type": "move",
            "parameters": {
                "mode": "walk",
                "forward": 1.0,
                "strafe": 0.0,
            },
        }
        spatial.begin_action(action)

        second = frame(2, "b", blocked=True)
        spatial.finish_action(action, True, 0.9, second)
        spatial.observe(second)
        model.update(second)

        directive = spatial.backtrack_directive(
            model,
            revisit_ratio=0.8,
            force=True,
        )
        self.assertIsNotNone(directive)
        self.assertEqual(directive.kind, "move")
        self.assertEqual(directive.maneuver, "back")
        self.assertIsNotNone(directive.target_place)

    def test_heading_change_requires_turn_before_return(self) -> None:
        spatial = SpatialMemory()
        model = EgocentricWorldModel()
        first = frame(1, "a")
        spatial.observe(first)
        spatial.begin_action({
            "type": "move",
            "parameters": {"forward": 1.0, "strafe": 0.0},
        })
        second = frame(2, "b", blocked=True)
        spatial.finish_action(
            {"type": "move", "parameters": {"forward": 1.0, "strafe": 0.0}},
            True,
            0.9,
            second,
        )
        spatial.observe(second)
        spatial.begin_action({
            "type": "look",
            "parameters": {"yaw_delta_rad": 0.8, "pitch_delta_rad": 0.0},
        })
        spatial.finish_action(
            {"type": "look", "parameters": {"yaw_delta_rad": 0.8, "pitch_delta_rad": 0.0}},
            True,
            1.0,
            second,
        )
        model.update(second)
        directive = spatial.backtrack_directive(model, force=True)
        self.assertEqual(directive.kind, "turn")
        self.assertLess(directive.yaw_delta_rad, 0)


if __name__ == "__main__":
    unittest.main()
