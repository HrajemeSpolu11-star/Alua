from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
import time
from typing import Any

from .bridge_client import BridgeClient
from .config import Config
from .errors import BridgeHttpError, BridgeUnavailable, ProtocolError
from .goals import GoalCandidate, IntrinsicCurriculum, ReflexGoalSelector
from .learning import learn_from_motor_outcome, motor_success
from .memory import WorkingMemory
from .perception import PerceptionFrame, build_frame
from .policy import ExplorationPolicy
from .skills import SkillLibrary
from .store import Store


LOG = logging.getLogger("alua.runtime")


@dataclass(frozen=True, slots=True)
class StepResult:
    session_id: str
    session_changed: bool
    observations_processed: int
    outcomes_resolved: int
    action_submitted: bool
    decision_id: str | None
    goal_key: str | None = None
    skill_key: str | None = None


class Runtime:
    def __init__(
        self,
        config: Config,
        store: Store,
        bridge: BridgeClient | Any,
        policy: ExplorationPolicy | None = None,
        memory: WorkingMemory | None = None,
        curriculum: IntrinsicCurriculum | None = None,
        reflex: ReflexGoalSelector | None = None,
        skills: SkillLibrary | None = None,
    ):
        self.config = config
        self.store = store
        self.bridge = bridge
        self.policy = policy or ExplorationPolicy()
        self.memory = memory or WorkingMemory(capacity=32)
        self.curriculum = curriculum or IntrinsicCurriculum()
        self.reflex = reflex or ReflexGoalSelector()
        self.skills = skills or SkillLibrary()
        self.store.ensure_agent(config.agent_id)

    @staticmethod
    def _decision_id(
        agent_id: str,
        session_id: str,
        sequence: int,
        action_payload: dict[str, Any],
    ) -> str:
        encoded = json.dumps(
            [agent_id, session_id, sequence, action_payload],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return "mind-" + hashlib.sha256(encoded).hexdigest()[:32]

    def _resolve_motor_events(self, session_id: str, frame: PerceptionFrame) -> int:
        resolved = 0
        for event in frame.motor_events:
            expectation = self.store.resolve_expectation(
                agent_id=self.config.agent_id,
                session_id=session_id,
                bridge_action_sequence=event["source_sequence"],
                outcome=event,
                resolved_sequence=frame.sequence,
            )
            if expectation is None:
                continue

            succeeded = motor_success(event)
            learn_from_motor_outcome(
                self.store,
                self.config.agent_id,
                expectation,
                event,
                frame.sequence,
            )

            goal_key = expectation.get("goal_key")
            goal_kind = expectation.get("goal_kind")
            if isinstance(goal_key, str) and goal_key and isinstance(goal_kind, str) and goal_kind:
                self.store.record_goal_outcome(
                    agent_id=self.config.agent_id,
                    goal_key=goal_key,
                    kind=goal_kind,
                    subject_signature=expectation.get("target_signature"),
                    supported=succeeded,
                    sequence=frame.sequence,
                )

            self.skills.learn(
                self.store,
                self.config.agent_id,
                expectation,
                supported=succeeded,
                sequence=frame.sequence,
            )
            resolved += 1
        return resolved

    def _select_goal(
        self,
        frame: PerceptionFrame,
        novel_appearance_ids: set[str],
    ) -> tuple[GoalCandidate, bool]:
        reflex_goal = self.reflex.choose(frame, self.memory)
        if reflex_goal is not None:
            return reflex_goal, True
        return (
            self.curriculum.choose(
                frame,
                novel_appearance_ids,
                self.memory,
                lambda key: self.store.goal_stats(self.config.agent_id, key),
            ),
            False,
        )

    def step(self) -> StepResult:
        session = self.bridge.session()
        session_id = session["session_id"]
        changed = self.store.apply_session(self.config.agent_id, session_id)
        if changed:
            self.memory.clear()

        state = self.store.state(self.config.agent_id)
        cursor = int(state["last_observation_sequence"])

        observations = self.bridge.observations(cursor)
        latest: PerceptionFrame | None = None
        latest_novel: set[str] = set()
        processed = 0
        outcomes_resolved = 0

        for observation in observations:
            frame = build_frame(observation)
            if frame.sequence <= cursor:
                raise ProtocolError("Bridge vrátil duplicitní nebo klesající observation sequence")

            seen = self.store.seen_appearance_ids(self.config.agent_id, frame.appearance_ids)
            current_novel = set(frame.appearance_ids) - seen
            outcomes_resolved += self._resolve_motor_events(session_id, frame)

            if self.store.record_observation(self.config.agent_id, session_id, frame):
                processed += 1
                self.memory.add(frame)
                latest = frame
                latest_novel = current_novel
                cursor = frame.sequence

            self.store.expire_old_expectations(
                self.config.agent_id,
                session_id,
                frame.sequence,
            )

        if latest is None:
            return StepResult(session_id, changed, processed, outcomes_resolved, False, None)

        if self.store.pending_expectation_count(self.config.agent_id, session_id) > 0:
            return StepResult(session_id, changed, processed, outcomes_resolved, False, None)

        goal, is_reflex = self._select_goal(latest, latest_novel)
        skill_key: str | None = None

        retrieved = None if is_reflex else self.skills.retrieve(
            self.store,
            self.config.agent_id,
            goal,
        )
        if retrieved is not None:
            skill_key, intent = retrieved
        else:
            intent = self.policy.choose(latest, goal, self.memory)

        action: dict[str, Any] = {
            "schema_version": 1,
            "agent_id": self.config.agent_id,
            "client_action_id": "",
            "type": intent.action_type,
            "parameters": intent.parameters,
        }
        if intent.duration is not None:
            action["duration"] = float(intent.duration)
        if intent.target_ref is not None:
            action["target_ref"] = intent.target_ref

        decision_id = self._decision_id(
            self.config.agent_id,
            session_id,
            latest.sequence,
            {key: value for key, value in action.items() if key != "client_action_id"},
        )
        action["client_action_id"] = decision_id

        rationale = dict(intent.rationale)
        if goal.reason:
            rationale["goal_reason"] = goal.reason

        self.store.record_decision(
            decision_id,
            self.config.agent_id,
            session_id,
            latest.sequence,
            action,
            rationale,
            goal_key=goal.key,
            goal_kind=goal.kind,
            skill_key=skill_key,
        )
        try:
            response = self.bridge.submit_action(action)
        except BridgeHttpError as exc:
            if exc.code != "target_expired":
                raise
            self.store.mark_decision_rejected(decision_id, "stale_target")
            LOG.info(
                "Zahozen zastaralý target_ref z observation %s; čekám na čerstvý vjem",
                latest.sequence,
            )
            return StepResult(
                session_id,
                changed,
                processed,
                outcomes_resolved,
                False,
                decision_id,
                goal.key,
                skill_key,
            )

        self.store.mark_decision_submitted(
            decision_id,
            response["request_id"],
            response["status"],
            response["action_sequence"],
        )
        self.store.record_goal_attempt(
            agent_id=self.config.agent_id,
            goal_key=goal.key,
            kind=goal.kind,
            subject_signature=goal.target_signature,
            priority=goal.priority,
            sequence=latest.sequence,
        )
        self.store.record_expectation(
            decision_id=decision_id,
            agent_id=self.config.agent_id,
            session_id=session_id,
            bridge_action_sequence=response["action_sequence"],
            action_type=intent.action_type,
            target_signature=intent.target_signature,
            action=action,
            created_sequence=latest.sequence,
            goal_key=goal.key,
            goal_kind=goal.kind,
            skill_key=skill_key,
        )
        return StepResult(
            session_id,
            changed,
            processed,
            outcomes_resolved,
            True,
            decision_id,
            goal.key,
            skill_key,
        )

    def run_forever(self) -> None:
        backoff = self.config.poll_interval
        while True:
            try:
                self.step()
                backoff = self.config.poll_interval
                time.sleep(self.config.poll_interval)
            except BridgeUnavailable as exc:
                LOG.warning("AluaBridge není dostupný: %s", exc)
                time.sleep(backoff)
                backoff = min(5.0, max(self.config.poll_interval, backoff * 2))
            except BridgeHttpError as exc:
                if not exc.retryable:
                    raise
                LOG.warning("Dočasná chyba AluaBridge: %s", exc)
                time.sleep(backoff)
                backoff = min(5.0, max(self.config.poll_interval, backoff * 2))
