from __future__ import annotations

from typing import Any

from .critic import BehaviorCritic
from .goals import GoalCandidate
from .memory import WorkingMemory
from .navigation import LocalNavigator
from .perception import PerceptionFrame
from .planning import BehaviorPlan, BoundedPlanner
from .policy import ActionIntent, ExplorationPolicy
from .world_model import EgocentricWorldModel


class ExecutiveController:
    """Hierarchical executive over curriculum goals and primitive actions."""

    def __init__(
        self,
        *,
        fallback_policy: ExplorationPolicy | None = None,
        world_model: EgocentricWorldModel | None = None,
        navigator: LocalNavigator | None = None,
        critic: BehaviorCritic | None = None,
        planner: BoundedPlanner | None = None,
    ) -> None:
        self.fallback_policy = fallback_policy or ExplorationPolicy()
        self.world_model = world_model or EgocentricWorldModel()
        self.navigator = navigator or LocalNavigator()
        self.critic = critic or BehaviorCritic()
        self.planner = planner or BoundedPlanner()
        self.active_plan: BehaviorPlan | None = None
        self.step_index = 0

    def reset_session(self) -> None:
        self.world_model.reset()
        self.navigator.reset()
        self.critic.reset()
        self.active_plan = None
        self.step_index = 0

    def observe(
        self,
        frame: PerceptionFrame,
        novel_appearance_ids: set[str] | None = None,
    ) -> None:
        self.world_model.update(frame, novel_appearance_ids)

    def _replace_plan(
        self,
        goal: GoalCandidate,
        frame: PerceptionFrame,
    ) -> BehaviorPlan:
        critique = self.critic.assess()
        self.active_plan = self.planner.plan(
            goal,
            frame,
            self.world_model,
            critique,
        )
        self.step_index = 0
        return self.active_plan

    def _current_plan(
        self,
        goal: GoalCandidate,
        frame: PerceptionFrame,
    ) -> BehaviorPlan:
        critique = self.critic.assess()
        plan = self.active_plan
        incompatible = (
            plan is None
            or self.step_index >= len(plan.steps)
            or plan.goal_key != goal.key
            or plan.goal_kind != goal.kind
            or critique.force_replan
        )
        if not incompatible and plan is not None:
            step = plan.steps[self.step_index].kind
            if (
                step == "navigate_frontier"
                and self.world_model.front_is_blocked()
                and plan.skill_name == "explore_frontier"
            ):
                incompatible = True
        if incompatible:
            plan = self._replace_plan(goal, frame)
        return plan

    def allow_reusable_skill(
        self,
        goal: GoalCandidate,
        frame: PerceptionFrame,
    ) -> bool:
        critique = self.critic.assess()
        if critique.force_replan:
            return False
        if goal.kind != "explore":
            return True
        if self.world_model.front_is_blocked():
            return False
        return self.navigator.prefers_forward(self.world_model)

    def choose(
        self,
        frame: PerceptionFrame,
        goal: GoalCandidate,
        memory: WorkingMemory,
    ) -> ActionIntent:
        plan = self._current_plan(goal, frame)
        step = plan.steps[self.step_index]
        critique = self.critic.assess()

        if step.kind in {"retreat", "inspect", "scan"}:
            intent = self.fallback_policy.choose(frame, goal, memory)
        else:
            if step.kind == "navigate_lateral":
                mode = "lateral"
            elif step.kind == "navigate_escape":
                mode = "escape"
            else:
                mode = "frontier"
            choice = self.navigator.choose(self.world_model, mode=mode)
            intent = ActionIntent(
                action_type="move",
                parameters={
                    "forward": choice.forward,
                    "strafe": choice.strafe,
                    "duration_s": choice.duration_s,
                    "speed_fraction": choice.speed_fraction,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={
                    "policy": "hierarchical_local_navigation",
                    "goal_key": goal.key,
                    "goal_kind": goal.kind,
                    "goal_priority": goal.priority,
                    "observation_sequence": frame.sequence,
                    "maneuver": choice.maneuver,
                    "navigation_score": round(choice.score, 4),
                    **choice.reason,
                },
            )

        rationale = {
            **intent.rationale,
            "plan_id": plan.plan_id,
            "plan_skill": plan.skill_name,
            "plan_step": step.kind,
            "plan_step_index": self.step_index,
            "plan_length": len(plan.steps),
            "critic_reasons": list(critique.reasons),
            "world_model": self.world_model.diagnostic_summary(),
        }
        return ActionIntent(
            action_type=intent.action_type,
            parameters=dict(intent.parameters),
            duration=intent.duration,
            target_ref=intent.target_ref,
            target_signature=intent.target_signature,
            rationale=rationale,
        )

    def on_submitted(
        self,
        intent: ActionIntent,
        goal: GoalCandidate,
        sequence: int,
    ) -> None:
        self.critic.record_submission(intent.action_type, goal.kind, sequence)
        if intent.action_type == "move":
            self.navigator.record_maneuver(
                self.navigator.maneuver_from_parameters(intent.parameters)
            )

    def on_rejected(self, goal: GoalCandidate, reason: str) -> None:
        if self.active_plan and self.active_plan.goal_key == goal.key:
            self.active_plan = None
            self.step_index = 0

    def on_outcome(
        self,
        expectation: dict[str, Any],
        supported: bool,
    ) -> None:
        action = expectation.get("action")
        if isinstance(action, dict):
            self.navigator.observe_outcome(action, supported)
            self.critic.record_outcome(action, supported)

        plan = self.active_plan
        if plan is None:
            return
        goal_key = expectation.get("goal_key")
        goal_kind = expectation.get("goal_kind")
        if goal_key != plan.goal_key or goal_kind != plan.goal_kind:
            return
        if supported:
            self.step_index += 1
            if self.step_index >= len(plan.steps):
                self.active_plan = None
                self.step_index = 0
        else:
            self.active_plan = None
            self.step_index = 0
