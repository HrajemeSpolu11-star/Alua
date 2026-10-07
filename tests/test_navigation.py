from __future__ import annotations

import unittest

from alua.navigation import LocalNavigator
from alua.perception import build_frame
from alua.world_model import EgocentricWorldModel


def model() -> EgocentricWorldModel:
    frame = build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": 1,
        "simulation_time": 1.0,
        "channels": {
            "vision": {
                "rays": [
                    {
                        "appearance_id": "front",
                        "distance_fraction": 0.06,
                        "blocks_motion": True,
                    },
                    {
                        "appearance_id": "left",
                        "distance_fraction": 0.95,
                        "blocks_motion": False,
                    },
                    {
                        "appearance_id": "right",
                        "distance_fraction": 0.70,
                        "blocks_motion": False,
                    },
                    {"distance_fraction": 1.0, "empty": True},
                    {"distance_fraction": 1.0, "empty": True},
                ]
            }
        },
    })
    result = EgocentricWorldModel()
    result.update(frame, {"left"})
    return result


class NavigationTests(unittest.TestCase):
    def test_lateral_mode_chooses_open_side_instead_of_blocked_front(self) -> None:
        navigator = LocalNavigator()
        choice = navigator.choose(model(), mode="lateral")
        self.assertEqual(choice.maneuver, "left")
        self.assertLess(choice.strafe, 0)

    def test_partial_progress_is_treated_as_navigation_failure(self) -> None:
        navigator = LocalNavigator()
        world = model()
        partial_action = {
            "type": "move",
            "parameters": {"forward": 0.18, "strafe": -0.78},
        }
        navigator.observe_outcome(partial_action, False, quality=0.28)
        navigator.observe_outcome(partial_action, False, quality=0.31)
        choice = navigator.choose(world, mode="lateral")
        self.assertNotEqual(choice.maneuver, "left")

    def test_failed_maneuver_is_penalized_and_replanned(self) -> None:
        navigator = LocalNavigator()
        world = model()
        failed_action = {
            "type": "move",
            "parameters": {"forward": 0.18, "strafe": -0.78},
        }
        navigator.observe_outcome(failed_action, False)
        navigator.observe_outcome(failed_action, False)
        choice = navigator.choose(world, mode="lateral")
        self.assertNotEqual(choice.maneuver, "left")


if __name__ == "__main__":
    unittest.main()
