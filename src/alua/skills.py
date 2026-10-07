from __future__ import annotations

import hashlib
import json
from typing import Any

from .goals import GoalCandidate
from .perception import PerceptionFrame
from .policy import ActionIntent, available_effector, near_central_obstacle
from .store import Store, canonical_json, strip_ephemeral


SAFE_SKILL_ACTIONS = {"move", "manipulate"}
LEARNABLE_GOAL_KINDS = {"explore", "inspect_object"}


def _safe_step_from_action(action: dict[str, Any]) -> dict[str, Any] | None:
    action_type = action.get("type")
    parameters = action.get("parameters")
    if action_type not in SAFE_SKILL_ACTIONS or not isinstance(parameters, dict):
        return None
    if action_type == "manipulate" and parameters.get("verb") != "touch":
        return None
    safe_parameters = strip_ephemeral(parameters)
    if not isinstance(safe_parameters, dict):
        return None
    if action_type == "manipulate":
        # Konkrétní ruka je kontext těla, ne přenositelná část dovednosti.
        safe_parameters.pop("effector", None)
    step: dict[str, Any] = {
        "type": action_type,
        "parameters": safe_parameters,
    }
    duration = action.get("duration")
    if isinstance(duration, (int, float)) and not isinstance(duration, bool):
        step["duration"] = float(duration)
    return step


class SkillLibrary:
    """Reusable, data-only motor skills learned from verified outcomes.

    Skills are action templates, never executable Python/JavaScript. target_ref
    is deliberately absent from persistence and is rebound from the live goal.
    """

    min_successes = 3
    min_confidence = 0.70

    def reconcile(self, store: Store, agent_id: str) -> int:
        """Deactivate legacy reusable skills that current policy no longer permits."""
        return store.deactivate_reusable_skills_outside(
            agent_id,
            frozenset(LEARNABLE_GOAL_KINDS),
        )

    @staticmethod
    def skill_key(goal_kind: str, target_signature: str | None, step: dict[str, Any]) -> str:
        payload = canonical_json({
            "goal_kind": goal_kind,
            "target_signature": target_signature,
            "step": strip_ephemeral(step),
        }).encode("utf-8")
        return "skill-" + hashlib.sha256(payload).hexdigest()[:24]

    def retrieve(
        self,
        store: Store,
        agent_id: str,
        goal: GoalCandidate,
        frame: PerceptionFrame | None = None,
    ) -> tuple[str, ActionIntent] | None:
        if goal.kind.startswith("survive_") or goal.kind not in LEARNABLE_GOAL_KINDS:
            return None
        if goal.kind == "explore" and frame is not None and near_central_obstacle(frame):
            # Kontextově slepý forward skill nesmí přebít aktuální obstacle bypass.
            return None
        record = store.best_reusable_skill(
            agent_id=agent_id,
            goal_kind=goal.kind,
            target_signature=goal.target_signature,
        )
        if not record:
            return None
        steps = record.get("steps")
        if not isinstance(steps, list) or len(steps) != 1 or not isinstance(steps[0], dict):
            return None
        step = steps[0]
        action_type = step.get("type")
        parameters = step.get("parameters")
        if action_type not in SAFE_SKILL_ACTIONS or not isinstance(parameters, dict):
            return None
        rebound_parameters = dict(parameters)
        if action_type == "manipulate":
            if rebound_parameters.get("verb") != "touch" or not goal.target_ref:
                return None
            rebound_parameters.pop("effector", None)
            if frame is not None:
                effector = available_effector(frame, "touch")
                if effector is not None:
                    rebound_parameters["effector"] = effector
        return (
            record["skill_key"],
            ActionIntent(
                action_type=action_type,
                parameters=rebound_parameters,
                duration=step.get("duration") if isinstance(step.get("duration"), (int, float)) else None,
                target_ref=goal.target_ref if action_type == "manipulate" else None,
                target_signature=goal.target_signature,
                rationale={
                    "policy": "reusable_skill",
                    "goal_key": goal.key,
                    "goal_kind": goal.kind,
                    "skill_key": record["skill_key"],
                    "skill_confidence": record["confidence"],
                    "skill_successes": record["success_count"],
                    "skill_failures": record["failure_count"],
                },
            ),
        )

    def learn(
        self,
        store: Store,
        agent_id: str,
        expectation: dict[str, Any],
        *,
        supported: bool,
        sequence: int,
    ) -> dict[str, Any] | None:
        goal_kind = expectation.get("goal_kind")
        if (
            not isinstance(goal_kind, str)
            or not goal_kind
            or goal_kind.startswith("survive_")
            or goal_kind not in LEARNABLE_GOAL_KINDS
        ):
            return None
        action = expectation.get("action")
        if not isinstance(action, dict):
            return None
        step = _safe_step_from_action(action)
        if step is None:
            return None
        if goal_kind == "explore":
            parameters = step.get("parameters", {})
            forward = parameters.get("forward")
            strafe = parameters.get("strafe")
            mode = parameters.get("mode", "walk")
            if (
                mode != "walk"
                or not isinstance(forward, (int, float))
                or isinstance(forward, bool)
                or not isinstance(strafe, (int, float))
                or isinstance(strafe, bool)
                or float(forward) < 0.5
                or abs(float(strafe)) > 0.05
            ):
                # Obstacle-bypass i terénní režimy (jump/vault/climb/swim/...)
                # jsou kontextové motorické reakce, ne univerzální explore skill.
                # Bez precondition modelu se nesmí přenést do jiného terénu.
                return None
        target_signature = expectation.get("target_signature")
        if not isinstance(target_signature, str):
            target_signature = None
        skill_key = self.skill_key(goal_kind, target_signature, step)
        return store.update_skill_evidence(
            agent_id=agent_id,
            skill_key=skill_key,
            kind=step["type"],
            goal_kind=goal_kind,
            target_signature=target_signature,
            steps=[step],
            supported=supported,
            sequence=sequence,
            min_successes=self.min_successes,
            min_confidence=self.min_confidence,
        )
