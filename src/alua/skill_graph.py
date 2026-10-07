from __future__ import annotations

from dataclasses import dataclass

from .critic import Critique
from .goals import GoalCandidate
from .world_model import EgocentricWorldModel


@dataclass(frozen=True, slots=True)
class SkillDefinition:
    name: str
    goal_kinds: frozenset[str]
    steps: tuple[str, ...]
    description: str


class SkillGraph:
    """Safe, data-only hierarchy of reusable behavioral building blocks.

    The graph contains no executable generated code. Learned single-action
    skills continue to live in SkillLibrary; this layer composes stable motor
    primitives into bounded behaviors.
    """

    def __init__(self) -> None:
        self._skills = {
            "survive_retreat": SkillDefinition(
                "survive_retreat",
                frozenset({"survive_damage"}),
                ("retreat",),
                "create distance from an immediate damage signal",
            ),
            "inspect_by_touch": SkillDefinition(
                "inspect_by_touch",
                frozenset({"inspect_object"}),
                ("inspect",),
                "touch a currently reachable uncertain percept",
            ),
            "scan_environment": SkillDefinition(
                "scan_environment",
                frozenset({"scan_obstacle", "scan_recovery", "scan_periodic"}),
                ("scan",),
                "perform one bounded information-gathering head movement",
            ),
            "explore_frontier": SkillDefinition(
                "explore_frontier",
                frozenset({"explore"}),
                ("navigate_frontier",),
                "move toward the best currently perceived local frontier",
            ),
            "bypass_obstacle": SkillDefinition(
                "bypass_obstacle",
                frozenset({"explore"}),
                ("navigate_lateral", "navigate_frontier"),
                "use a lateral step and then resume frontier motion",
            ),
            "escape_stagnation": SkillDefinition(
                "escape_stagnation",
                frozenset({"explore"}),
                ("navigate_escape", "navigate_frontier"),
                "break a repeated-failure pattern before resuming exploration",
            ),
        }

    def get(self, name: str) -> SkillDefinition:
        return self._skills[name]

    def resolve(
        self,
        goal: GoalCandidate,
        model: EgocentricWorldModel,
        critique: Critique,
    ) -> SkillDefinition:
        if goal.kind == "survive_damage":
            return self.get("survive_retreat")
        if goal.kind == "inspect_object":
            return self.get("inspect_by_touch")
        if goal.kind in {"scan_obstacle", "scan_recovery", "scan_periodic"}:
            return self.get("scan_environment")
        if goal.kind == "explore":
            if critique.force_replan:
                return self.get("escape_stagnation")
            if model.front_is_blocked():
                return self.get("bypass_obstacle")
            return self.get("explore_frontier")
        return self.get("explore_frontier")
