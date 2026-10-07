from __future__ import annotations

import unittest

from alua.critic import Critique
from alua.goals import GoalCandidate
from alua.perception import build_frame
from alua.planning import BoundedPlanner
from alua.world_model import EgocentricWorldModel


def blocked_model() -> tuple[object, EgocentricWorldModel]:
    frame = build_frame({
        "schema_version": 1,
        "agent_id": "alua:1",
        "sequence": 7,
        "simulation_time": 7.0,
        "channels": {
            "vision": {
                "rays": [
                    {"distance_fraction": 0.05, "appearance_id": "front", "blocks_motion": True},
                    {"distance_fraction": 0.8, "appearance_id": "left", "blocks_motion": False},
                    {"distance_fraction": 0.7, "appearance_id": "right", "blocks_motion": False},
                ]
            }
        },
    })
    model = EgocentricWorldModel()
    model.update(frame)
    return frame, model


class PlanningTests(unittest.TestCase):
    def test_blocked_exploration_becomes_bounded_composite_skill(self) -> None:
        frame, model = blocked_model()
        plan = BoundedPlanner().plan(
            GoalCandidate("explore:open", "explore", 0.5),
            frame,
            model,
            Critique(False, False, ()),
        )
        self.assertEqual(plan.skill_name, "bypass_obstacle")
        self.assertEqual(
            tuple(step.kind for step in plan.steps),
            ("navigate_lateral", "navigate_frontier"),
        )
        self.assertLessEqual(len(plan.steps), 4)

    def test_stagnation_uses_escape_skill(self) -> None:
        frame, model = blocked_model()
        plan = BoundedPlanner().plan(
            GoalCandidate("explore:open", "explore", 0.5),
            frame,
            model,
            Critique(True, True, ("poor_move_progress",)),
        )
        self.assertEqual(plan.skill_name, "escape_stagnation")
        self.assertEqual(
            tuple(step.kind for step in plan.steps),
            ("reorient_escape", "navigate_escape", "navigate_frontier"),
        )


    def test_body_need_goals_have_bounded_non_exploration_skills(self) -> None:
        frame, model = blocked_model()
        planner = BoundedPlanner()
        surface = planner.plan(
            GoalCandidate("survive:breath", "survive_breath", 1.25),
            frame,
            model,
            Critique(False, False, ()),
        )
        self.assertEqual(surface.skill_name, "survive_surface")
        self.assertEqual(tuple(step.kind for step in surface.steps), ("surface",))

        consume = planner.plan(
            GoalCandidate("need:consume:pfood", "satisfy_hunger", 0.9),
            frame,
            model,
            Critique(False, False, ()),
        )
        self.assertEqual(consume.skill_name, "satisfy_body_need")

        mining = planner.plan(
            GoalCandidate("need:mine:pfood", "acquire_required_resource", 0.9),
            frame,
            model,
            Critique(False, False, ()),
        )
        self.assertEqual(mining.skill_name, "acquire_required_resource")
        self.assertEqual(tuple(step.kind for step in mining.steps), ("resource",))


if __name__ == "__main__":
    unittest.main()
