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

    def test_backtrack_success_does_not_create_new_outward_route(self) -> None:
        spatial = SpatialMemory()
        model = EgocentricWorldModel()
        start = frame(1, "origin")
        spatial.observe(start)
        departure = {"type": "move", "parameters": {"mode": "walk", "forward": 1.0, "strafe": 0.0}}
        spatial.begin_action(departure)
        distant = frame(2, "destination", blocked=True)
        spatial.finish_action(departure, True, .90, distant)
        spatial.observe(distant)
        model.update(distant)
        self.assertEqual(len(spatial._route), 1)
        expected_origin = spatial._route[0].origin
        self.assertIsNotNone(spatial.backtrack_directive(model, force=True))

        # Physically successful inverse movement but still no sensory match
        # to the predecessor. This MUST NOT create an outbound C->B route.
        returning = {"type": "move", "parameters": {"mode": "walk", "forward": -0.65, "strafe": 0.0}}
        unexpected = frame(3, "aliased-neighbor", blocked=True)
        spatial.begin_action(returning)
        spatial.finish_action(returning, True, .92, unexpected, goal_kind="spatial_backtrack")
        spatial.observe(unexpected)
        model.update(unexpected)
        self.assertEqual(len(spatial._route), 1)
        self.assertEqual(spatial._route[0].origin, expected_origin)
        self.assertTrue(spatial.diagnostics()["backtracking"])

    def test_backtrack_abandons_unrecognized_route_after_bounded_real_attempts(self) -> None:
        spatial = SpatialMemory()
        model = EgocentricWorldModel()
        start = frame(1, "origin")
        spatial.observe(start)
        departure = {"type": "move", "parameters": {"mode": "walk", "forward": 1.0, "strafe": 0.0}}
        spatial.begin_action(departure)
        distant = frame(2, "destination", blocked=True)
        spatial.finish_action(departure, True, .90, distant)
        spatial.observe(distant)
        model.update(distant)
        self.assertIsNotNone(spatial.backtrack_directive(model, force=True))

        returning = {"type": "move", "parameters": {"mode": "walk", "forward": -0.65, "strafe": 0.0}}
        for i in range(8):
            # Different perceptual context each time, never recognizes origin.
            sensed = frame(3 + i, f"unrecognized-{i}", blocked=True)
            spatial.begin_action(returning)
            spatial.finish_action(returning, True, .84, sensed, goal_kind="spatial_backtrack")
            spatial.observe(sensed)
            model.update(sensed)
            self.assertEqual(len(spatial._route), 1)
            if i < 7:
                self.assertIsNotNone(spatial.backtrack_directive(model, force=True))

        self.assertIsNone(spatial.backtrack_directive(model, force=True))
        self.assertEqual(len(spatial._route), 0)
        self.assertFalse(spatial.diagnostics()["backtracking"])

    def test_backtrack_route_pops_only_when_original_percept_reappears(self) -> None:
        spatial = SpatialMemory()
        model = EgocentricWorldModel()
        start = frame(1, "origin")
        spatial.observe(start)
        depart = {"type": "move", "parameters": {"mode": "walk", "forward": 1.0, "strafe": 0.0}}
        spatial.begin_action(depart)
        distant = frame(2, "destination", blocked=True)
        spatial.finish_action(depart, True, .95, distant)
        spatial.observe(distant)
        model.update(distant)
        self.assertIsNotNone(spatial.backtrack_directive(model, force=True))

        return_action = {"type": "move", "parameters": {"mode": "walk", "forward": -0.65, "strafe": 0.0}}
        spatial.begin_action(return_action)
        original_again = frame(3, "origin")
        spatial.finish_action(
            return_action, True, .90, original_again,
            goal_kind="spatial_backtrack",
        )
        spatial.observe(original_again)
        self.assertEqual(len(spatial._route), 0)
        self.assertIsNone(spatial.backtrack_directive(model, force=True))
        self.assertFalse(spatial.diagnostics()["backtracking"])

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
