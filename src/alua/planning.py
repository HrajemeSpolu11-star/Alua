from __future__ import annotations

from dataclasses import dataclass
import hashlib

from .critic import Critique
from .goals import GoalCandidate
from .perception import PerceptionFrame
from .skill_graph import SkillGraph
from .world_model import EgocentricWorldModel


@dataclass(frozen=True, slots=True)
class PlanStep:
    kind: str


@dataclass(frozen=True, slots=True)
class BehaviorPlan:
    plan_id: str
    goal_key: str
    goal_kind: str
    skill_name: str
    steps: tuple[PlanStep, ...]
    created_sequence: int


class BoundedPlanner:
    """Small hierarchical planner with a hard step bound.

    High-level goals are mapped to safe data-only skills. Each skill expands to
    a short sequence of abstract controller steps; no arbitrary code generation
    or hidden world knowledge is involved.
    """

    def __init__(self, skill_graph: SkillGraph | None = None, max_steps: int = 4):
        if not 1 <= max_steps <= 8:
            raise ValueError("max_steps must be 1..8")
        self.skill_graph = skill_graph or SkillGraph()
        self.max_steps = max_steps

    def plan(
        self,
        goal: GoalCandidate,
        frame: PerceptionFrame,
        model: EgocentricWorldModel,
        critique: Critique,
    ) -> BehaviorPlan:
        skill = self.skill_graph.resolve(goal, model, critique)
        step_names = skill.steps[: self.max_steps]
        payload = (
            f"{goal.key}|{goal.kind}|{skill.name}|{frame.sequence}|"
            + ",".join(step_names)
        ).encode("utf-8")
        plan_id = "plan-" + hashlib.sha256(payload).hexdigest()[:20]
        return BehaviorPlan(
            plan_id=plan_id,
            goal_key=goal.key,
            goal_kind=goal.kind,
            skill_name=skill.name,
            steps=tuple(PlanStep(kind=name) for name in step_names),
            created_sequence=frame.sequence,
        )
