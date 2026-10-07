from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
import time
from typing import Any

from .bridge_client import BridgeClient
from .config import Config
from .cognition import CognitiveCore, CognitiveSnapshot
from .errors import BridgeHttpError, BridgeUnavailable, ProtocolError
from .executive import ExecutiveController
from .goals import GoalCandidate, IntrinsicCurriculum, ReflexGoalSelector
from .learning import learn_from_motor_outcome, motor_quality, motor_success
from .memory import WorkingMemory
from .perception import PerceptionFrame, build_frame
from .policy import ExplorationPolicy
from .skills import SkillLibrary
from .store import Store
from .topology import PerceptualTopology
from .utility import AdaptiveUtilityModel


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
        executive: ExecutiveController | None = None,
        topology: PerceptualTopology | None = None,
        utility: AdaptiveUtilityModel | None = None,
        cognitive: CognitiveCore | None = None,
    ):
        self.config = config
        self.store = store
        self.bridge = bridge
        self.policy = policy or ExplorationPolicy()
        self.memory = memory or WorkingMemory(capacity=32)
        self.curriculum = curriculum or IntrinsicCurriculum()
        self.reflex = reflex or ReflexGoalSelector()
        self.skills = skills or SkillLibrary()
        self.executive = executive or ExecutiveController(fallback_policy=self.policy)
        self.topology = topology or PerceptualTopology()
        self.utility = utility or AdaptiveUtilityModel()
        self.cognitive = cognitive or CognitiveCore()
        self.store.ensure_agent(config.agent_id)
        deactivated = self.skills.reconcile(self.store, config.agent_id)
        if deactivated:
            LOG.info("Deaktivováno %s zastaralých reusable skills", deactivated)

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
            quality = motor_quality(event)
            action = expectation.get("action")
            if isinstance(action, dict):
                self.topology.finish_action(
                    self.store,
                    self.config.agent_id,
                    action,
                    succeeded,
                    frame,
                )
            self.cognitive.finish_action(
                expectation=expectation,
                event=event,
                frame=frame,
                supported=succeeded,
                progress=quality,
                memory=self.memory,
                store=self.store,
                agent_id=self.config.agent_id,
            )
            self.executive.on_outcome(
                expectation,
                succeeded,
                frame,
                quality=quality,
            )
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
        session_id: str,
        cognitive_snapshot: CognitiveSnapshot | None = None,
    ) -> tuple[GoalCandidate, bool]:
        reflex_goal = self.reflex.choose(frame, self.memory)
        if reflex_goal is not None:
            return reflex_goal, True

        if cognitive_snapshot is not None:
            directive = cognitive_snapshot.spatial_directive
            if directive is not None and directive.confidence >= 0.60:
                return (
                    GoalCandidate(
                        key=f"spatial:backtrack:{directive.target_place or 'previous'}",
                        kind="spatial_backtrack",
                        priority=min(1.20, 0.86 + 0.28 * directive.confidence),
                        reason={
                            "selector": "cognitive_core",
                            "phase": directive.kind,
                            "yaw_delta_rad": directive.yaw_delta_rad,
                            "maneuver": directive.maneuver,
                            "target_place": directive.target_place,
                            "confidence": directive.confidence,
                            "meta_reasons": list(cognitive_snapshot.meta.reasons),
                        },
                    ),
                    False,
                )
            if (
                cognitive_snapshot.deliberative_action is not None
                and cognitive_snapshot.meta.stagnation >= 0.52
            ):
                deliberation = cognitive_snapshot.deliberative_action.get(
                    "_deliberation",
                    {},
                )
                return (
                    GoalCandidate(
                        key=f"deliberate:{cognitive_snapshot.context_signature}",
                        kind="deliberate_navigation",
                        priority=min(
                            1.05,
                            0.72 + 0.30 * cognitive_snapshot.meta.stagnation,
                        ),
                        reason={
                            "selector": "cognitive_core",
                            "action": {
                                "type": cognitive_snapshot.deliberative_action.get("type"),
                                "parameters": cognitive_snapshot.deliberative_action.get("parameters"),
                            },
                            "deliberation": deliberation,
                            "meta_reasons": list(cognitive_snapshot.meta.reasons),
                        },
                    ),
                    False,
                )
        previous = self.store.latest_submitted_goal(
            self.config.agent_id,
            session_id,
        )
        previous_goal_kind = previous.get("goal_kind") if previous else None
        previous_action_type = previous.get("action_type") if previous else None
        information_need = self.executive.world_model.horizontal_uncertainty()

        def rank(candidate: GoalCandidate) -> float:
            stats = self.store.goal_stats(self.config.agent_id, candidate.key)
            score = self.utility.evaluate(
                candidate,
                stats=stats,
                memory=self.memory,
                information_need=information_need,
            ).total
            if cognitive_snapshot is not None:
                drives = cognitive_snapshot.drives
                if candidate.kind == "explore":
                    score += 0.24 * drives.exploration
                    score -= 0.18 * drives.frustration
                elif candidate.kind == "inspect_object":
                    score += 0.22 * drives.curiosity
                elif candidate.kind in {
                    "scan_obstacle",
                    "scan_recovery",
                    "scan_periodic",
                }:
                    score += 0.16 * cognitive_snapshot.meta.uncertainty
                elif candidate.kind in {
                    "satisfy_hunger",
                    "satisfy_thirst",
                    "recover_stamina",
                }:
                    score += 0.25 * drives.homeostasis
            return score

        return (
            self.curriculum.choose(
                frame,
                novel_appearance_ids,
                self.memory,
                lambda key: self.store.goal_stats(self.config.agent_id, key),
                previous_goal_kind=previous_goal_kind
                if isinstance(previous_goal_kind, str)
                else None,
                previous_action_type=previous_action_type
                if isinstance(previous_action_type, str)
                else None,
                information_need=information_need,
                candidate_ranker=rank,
                belief_lookup=lambda key: self.store.belief(
                    self.config.agent_id,
                    key,
                ),
            ),
            False,
        )

    def step(self) -> StepResult:
        session = self.bridge.session()
        session_id = session["session_id"]
        changed = self.store.apply_session(self.config.agent_id, session_id)
        if changed:
            self.memory.clear()
            self.executive.reset_session()
            self.topology.reset_session()
            self.cognitive.reset_session()

        state = self.store.state(self.config.agent_id)
        cursor = int(state["last_observation_sequence"])

        observations = self.bridge.observations(cursor)
        latest: PerceptionFrame | None = None
        latest_novel: set[str] = set()
        latest_cognitive: CognitiveSnapshot | None = None
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
                self.executive.observe(frame, current_novel)
                self.topology.observe(self.store, self.config.agent_id, frame)
                self.executive.set_navigation_priors(
                    self.topology.persistent_penalties(
                        self.store,
                        self.config.agent_id,
                    )
                )
                latest_cognitive = self.cognitive.observe(
                    frame=frame,
                    novel_appearance_ids=current_novel,
                    memory=self.memory,
                    world_model=self.executive.world_model,
                    topology=self.topology,
                    store=self.store,
                    agent_id=self.config.agent_id,
                    session_id=session_id,
                )
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

        goal, is_reflex = self._select_goal(
            latest,
            latest_novel,
            session_id,
            latest_cognitive,
        )
        skill_key: str | None = None

        retrieved = None
        if (
            not is_reflex
            and self.executive.allow_reusable_skill(goal, latest)
        ):
            retrieved = self.skills.retrieve(
                self.store,
                self.config.agent_id,
                goal,
                latest,
            )
        if retrieved is not None:
            skill_key, intent = retrieved
        else:
            intent = self.executive.choose(latest, goal, self.memory)

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
        if latest_cognitive is not None:
            rationale["cognitive_state"] = latest_cognitive.diagnostics()

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
            self.executive.on_rejected(goal, "stale_target")
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
        self.executive.on_submitted(intent, goal, latest.sequence)
        self.topology.begin_action(action)
        self.cognitive.begin_action(action)
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
