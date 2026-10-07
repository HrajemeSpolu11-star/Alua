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
            "survive_surface": SkillDefinition(
                "survive_surface",
                frozenset({"survive_breath"}),
                ("surface",),
                "swim upward when breath becomes critical",
            ),
            "recover_body": SkillDefinition(
                "recover_body",
                frozenset({"recover_stamina"}),
                ("recover",),
                "reduce exertion and recover bodily capacity",
            ),
            "satisfy_body_need": SkillDefinition(
                "satisfy_body_need",
                frozenset({"satisfy_thirst", "satisfy_hunger"}),
                ("need",),
                "act on thirst or hunger using current sensory evidence and learned effects",
            ),
            "collect_observed_object": SkillDefinition(
                "collect_observed_object",
                frozenset({"collect_object"}),
                ("collect",),
                "store one inspected reachable object for later experimentation",
            ),
            "acquire_required_resource": SkillDefinition(
                "acquire_required_resource",
                frozenset({"acquire_required_resource"}),
                ("resource",),
                "physically break a currently needed target only when a need-driven goal requests it",
            ),
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
                ("reorient_escape", "navigate_escape", "navigate_frontier"),
                "rotate the body toward a better frontier, escape, then resume exploration",
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
        if goal.kind == "survive_breath":
            return self.get("survive_surface")
        if goal.kind == "survive_damage":
            return self.get("survive_retreat")
        if goal.kind == "recover_stamina":
            return self.get("recover_body")
        if goal.kind in {"satisfy_thirst", "satisfy_hunger"}:
            return self.get("satisfy_body_need")
        if goal.kind == "collect_object":
            return self.get("collect_observed_object")
        if goal.kind == "acquire_required_resource":
            return self.get("acquire_required_resource")
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
