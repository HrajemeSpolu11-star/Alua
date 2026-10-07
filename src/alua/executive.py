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
        self._navigation_priors: dict[str, float] = {}
        self._escape_turn_index = 0

    def reset_session(self) -> None:
        self.world_model.reset()
        self.navigator.reset()
        self.critic.reset()
        self.active_plan = None
        self.step_index = 0
        self._navigation_priors = {}
        self._escape_turn_index = 0

    def set_navigation_priors(self, penalties: dict[str, float] | None) -> None:
        self._navigation_priors = {
            key: max(0.0, float(value))
            for key, value in (penalties or {}).items()
            if key in {"forward", "left", "right", "back"}
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
        }

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
        critique_requires_new_plan = (
            critique.force_replan
            and (plan is None or plan.skill_name != "escape_stagnation")
        )
        incompatible = (
            plan is None
            or self.step_index >= len(plan.steps)
            or plan.goal_key != goal.key
            or plan.goal_kind != goal.kind
            or critique_requires_new_plan
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
        return self.navigator.prefers_forward(
            self.world_model,
            persistent_penalties=self._navigation_priors,
        )

    def choose(
        self,
        frame: PerceptionFrame,
        goal: GoalCandidate,
        memory: WorkingMemory,
    ) -> ActionIntent:
        plan = self._current_plan(goal, frame)
        step = plan.steps[self.step_index]
        critique = self.critic.assess()

        if step.kind in {
            "retreat",
            "inspect",
            "scan",
            "surface",
            "recover",
            "need",
            "collect",
            "resource",
            "backtrack",
            "deliberate",
        }:
            intent = self.fallback_policy.choose(frame, goal, memory)
        elif step.kind == "reorient_escape":
            left_score = (
                self.world_model.sector_score("left")
                - self._navigation_priors.get("left", 0.0)
            )
            right_score = (
                self.world_model.sector_score("right")
                - self._navigation_priors.get("right", 0.0)
            )
            if abs(left_score - right_score) < 0.05:
                turn_left = self._escape_turn_index % 2 == 0
            else:
                turn_left = left_score > right_score
            self._escape_turn_index += 1
            yaw_delta = 0.85 if turn_left else -0.85
            intent = ActionIntent(
                action_type="look",
                parameters={
                    "yaw_delta_rad": yaw_delta,
                    "pitch_delta_rad": 0.0,
                },
                duration=None,
                target_ref=None,
                target_signature=None,
                rationale={
                    "policy": "stagnation_reorientation",
                    "goal_key": goal.key,
                    "goal_kind": goal.kind,
                    "goal_priority": goal.priority,
                    "observation_sequence": frame.sequence,
                    "turn": "left" if turn_left else "right",
                    "left_score": round(left_score, 4),
                    "right_score": round(right_score, 4),
                },
            )
        else:
            terrain_intent = (
                self.fallback_policy.terrain_intent(frame, goal, memory)
                if goal.kind == "explore"
                else None
            )
            if terrain_intent is not None:
                intent = terrain_intent
            else:
                if step.kind == "navigate_lateral":
                    mode = "lateral"
                elif step.kind == "navigate_escape":
                    mode = "escape"
                else:
                    mode = "frontier"
                choice = self.navigator.choose(
                    self.world_model,
                    mode=mode,
                    persistent_penalties=self._navigation_priors,
                )
                intent = ActionIntent(
                    action_type="move",
                    parameters={
                        "mode": "walk",
                        "forward": choice.forward,
                        "strafe": choice.strafe,
                        "vertical": 0.0,
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
        if intent.rationale.get("policy") == "reusable_skill":
            # Learned primitive reuse is an execution shortcut outside the
            # current macro plan; never advance a stale macro from its outcome.
            self.active_plan = None
            self.step_index = 0
        maneuver: str | None = None
        if intent.action_type == "move":
            maneuver = self.navigator.maneuver_from_parameters(intent.parameters)
            self.navigator.record_maneuver(maneuver)
        self.critic.record_submission(
            intent.action_type,
            goal.kind,
            sequence,
            maneuver=maneuver,
        )

    def on_rejected(self, goal: GoalCandidate, reason: str) -> None:
        if self.active_plan and self.active_plan.goal_key == goal.key:
            self.active_plan = None
            self.step_index = 0

    def on_outcome(
        self,
        expectation: dict[str, Any],
        supported: bool,
        frame: PerceptionFrame | None = None,
        quality: float | None = None,
    ) -> None:
        action = expectation.get("action")
        if isinstance(action, dict):
            self.navigator.observe_outcome(action, supported, quality)
            self.critic.record_outcome(action, supported, quality)
            if supported and action.get("type") == "look":
                self.world_model.invalidate_view()

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
