from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .attention import AttentionState, AttentionSystem
from .causal import CausalLearner
from .consolidation import ConsolidationReport, MemoryConsolidator
from .drives import DriveState, DriveSystem
from .memory import WorkingMemory
from .metacognition import MetaState, Metacognition
from .object_memory import ObjectMemory
from .perception import PerceptionFrame
from .predictive import PredictiveModel, action_signature
from .prospective import ProspectiveIntent, ProspectiveMemory
from .risk import RiskModel
from .self_model import SelfModel
from .social import SocialCognition
from .spatial_memory import SpatialDirective, SpatialMemory
from .store import Store
from .topology import PerceptualTopology
from .world_model import EgocentricWorldModel


@dataclass(frozen=True, slots=True)
class CognitiveSnapshot:
    context_signature: str
    attention: AttentionState
    meta: MetaState
    drives: DriveState
    spatial_directive: SpatialDirective | None
    deliberative_action: dict[str, Any] | None
    prospective_intents: tuple[ProspectiveIntent, ...]
    self_state: dict[str, float]
    social_entities: int
    consolidation: ConsolidationReport | None

    def diagnostics(self) -> dict[str, Any]:
        return {
            "context_signature": self.context_signature,
            "attention": {
                "kind": self.attention.focus_kind,
                "signature": self.attention.focus_signature,
                "ray": self.attention.focus_ray,
                "salience": round(self.attention.salience, 4),
                "surprise": round(self.attention.surprise, 4),
                "uncertainty": round(self.attention.uncertainty, 4),
            },
            "metacognition": {
                "stagnation": round(self.meta.stagnation, 4),
                "loop_risk": round(self.meta.loop_risk, 4),
                "uncertainty": round(self.meta.uncertainty, 4),
                "prediction_surprise": round(
                    self.meta.prediction_surprise,
                    4,
                ),
                "recommended_mode": self.meta.recommended_mode,
                "reasons": list(self.meta.reasons),
            },
            "drives": {
                "safety": round(self.drives.safety, 4),
                "homeostasis": round(self.drives.homeostasis, 4),
                "curiosity": round(self.drives.curiosity, 4),
                "frustration": round(self.drives.frustration, 4),
                "exploration": round(self.drives.exploration, 4),
            },
            "spatial_directive": (
                {
                    "kind": self.spatial_directive.kind,
                    "reason": self.spatial_directive.reason,
                    "yaw_delta_rad": round(
                        self.spatial_directive.yaw_delta_rad,
                        4,
                    ),
                    "maneuver": self.spatial_directive.maneuver,
                    "target_place": self.spatial_directive.target_place,
                    "confidence": round(
                        self.spatial_directive.confidence,
                        4,
                    ),
                }
                if self.spatial_directive
                else None
            ),
            "deliberative_action": self.deliberative_action,
            "prospective_intents": [
                {
                    "key": item.key,
                    "kind": item.kind,
                    "priority": item.priority,
                    "trigger_place": item.trigger_place,
                }
                for item in self.prospective_intents[:8]
            ],
            "self_state": {
                key: round(value, 4)
                for key, value in self.self_state.items()
            },
            "social_entities": self.social_entities,
        }


class CognitiveCore:
    """Coordinates higher cognition without bypassing existing boundaries."""

    def __init__(self) -> None:
        self.attention = AttentionSystem()
        self.objects = ObjectMemory()
        self.spatial = SpatialMemory()
        self.predictive = PredictiveModel()
        self.risk = RiskModel()
        self.self_model = SelfModel()
        self.causal = CausalLearner()
        self.meta = Metacognition()
        self.drives = DriveSystem()
        self.prospective = ProspectiveMemory()
        self.social = SocialCognition()
        self.consolidator = MemoryConsolidator()
        self.snapshot: CognitiveSnapshot | None = None
        self._pending_context: str | None = None
        self._pending_action: dict[str, Any] | None = None

    def reset_session(self) -> None:
        self.attention.reset_session()
        self.objects.reset_session()
        self.spatial.reset_session()
        self.meta.reset_session()
        self.snapshot = None
        self._pending_context = None
        self._pending_action = None

    @staticmethod
    def _candidate_actions() -> list[dict[str, Any]]:
        return [
            {
                "type": "move",
                "parameters": {
                    "mode": "walk",
                    "forward": 1.0,
                    "strafe": 0.0,
                    "vertical": 0.0,
                    "duration_s": 0.32,
                    "speed_fraction": 0.45,
                },
            },
            {
                "type": "move",
                "parameters": {
                    "mode": "walk",
                    "forward": 0.15,
                    "strafe": -0.75,
                    "vertical": 0.0,
                    "duration_s": 0.32,
                    "speed_fraction": 0.42,
                },
            },
            {
                "type": "move",
                "parameters": {
                    "mode": "walk",
                    "forward": 0.15,
                    "strafe": 0.75,
                    "vertical": 0.0,
                    "duration_s": 0.32,
                    "speed_fraction": 0.42,
                },
            },
            {
                "type": "move",
                "parameters": {
                    "mode": "walk",
                    "forward": -0.65,
                    "strafe": 0.0,
                    "vertical": 0.0,
                    "duration_s": 0.32,
                    "speed_fraction": 0.40,
                },
            },
        ]

    def _deliberate(
        self,
        store: Store,
        *,
        agent_id: str,
        context_signature: str,
        meta: MetaState,
    ) -> dict[str, Any] | None:
        if meta.stagnation < 0.48 and meta.prediction_surprise < 0.55:
            return None
        actions = self._candidate_actions()
        risks = {
            action_signature(action): self.risk.estimate(
                store,
                agent_id=agent_id,
                context_signature=context_signature,
                action=action,
            ).score
            for action in actions
        }
        scored = self.predictive.counterfactual_scores(
            store,
            agent_id=agent_id,
            context_signature=context_signature,
            actions=actions,
            risk_penalties=risks,
        )
        if not scored:
            return None
        action, score, prediction = scored[0]
        result = {
            "type": action["type"],
            "parameters": dict(action["parameters"]),
            "_deliberation": {
                "score": round(score, 4),
                "expected_progress": round(
                    prediction.expected_progress,
                    4,
                ),
                "expected_success": round(
                    prediction.expected_success,
                    4,
                ),
                "model_confidence": round(
                    prediction.confidence,
                    4,
                ),
                "alternatives": len(scored),
            },
        }
        return result

    def observe(
        self,
        *,
        frame: PerceptionFrame,
        novel_appearance_ids: set[str],
        memory: WorkingMemory,
        world_model: EgocentricWorldModel,
        topology: PerceptualTopology,
        store: Store,
        agent_id: str,
        session_id: str,
    ) -> CognitiveSnapshot:
        attention = self.attention.assess(
            frame,
            novel_appearance_ids,
        )
        self.objects.observe(
            frame,
            store=store,
            agent_id=agent_id,
        )
        context_signature = self.spatial.observe(
            frame,
            store=store,
            agent_id=agent_id,
        )
        self.meta.observe_place(context_signature)

        revisit = topology.recent_revisit_ratio()
        dead_end_score = self.spatial.dead_end_score(
            world_model,
            revisit,
        )
        meta = self.meta.assess(
            sensory_uncertainty=max(
                attention.uncertainty,
                world_model.horizontal_uncertainty(),
            ),
            topology_revisit_ratio=revisit,
            dead_end_score=dead_end_score,
        )
        if dead_end_score >= 0.62:
            self.spatial.mark_current_dead_end(
                store,
                agent_id,
                frame.sequence,
            )

        directive = self.spatial.backtrack_directive(
            world_model,
            revisit_ratio=revisit,
            force=meta.recommended_mode == "backtrack",
        )
        drives = self.drives.assess(
            frame,
            memory,
            attention,
            meta,
        )
        social_entities = self.social.observe(
            frame,
            store,
            agent_id=agent_id,
        )
        due = self.prospective.due(
            store,
            agent_id=agent_id,
            current_place=context_signature,
        )
        deliberative = (
            None
            if directive is not None
            else self._deliberate(
                store,
                agent_id=agent_id,
                context_signature=context_signature,
                meta=meta,
            )
        )

        consolidation = None
        if self.consolidator.due(frame.sequence):
            consolidation = self.consolidator.consolidate(
                store,
                agent_id=agent_id,
                session_id=session_id,
                sequence=frame.sequence,
            )

        snapshot = CognitiveSnapshot(
            context_signature=context_signature,
            attention=attention,
            meta=meta,
            drives=drives,
            spatial_directive=directive,
            deliberative_action=deliberative,
            prospective_intents=due,
            self_state=self.self_model.body_state(frame),
            social_entities=len(social_entities),
            consolidation=consolidation,
        )
        self.snapshot = snapshot

        store.upsert_cognitive_record(
            agent_id=agent_id,
            record_key="cognition:last-state",
            record_kind="metacognitive_state",
            payload=snapshot.diagnostics(),
            sequence=frame.sequence,
            confidence=meta.confidence,
        )
        return snapshot

    def begin_action(self, action: dict[str, Any]) -> None:
        self._pending_context = self.spatial.current_place
        self._pending_action = action
        self.spatial.begin_action(action)
        self.meta.record_action(action)

    def finish_action(
        self,
        *,
        expectation: dict[str, Any],
        event: dict[str, Any],
        frame: PerceptionFrame,
        supported: bool,
        progress: float,
        memory: WorkingMemory,
        store: Store,
        agent_id: str,
    ) -> None:
        action = expectation.get("action")
        if not isinstance(action, dict):
            return
        context = (
            self._pending_context
            or self.spatial.current_place
            or "unknown-context"
        )
        progress = max(0.0, min(1.0, float(progress)))
        prediction = self.predictive.learn(
            store,
            agent_id=agent_id,
            context_signature=context,
            action=action,
            supported=supported,
            progress=progress,
            sequence=frame.sequence,
        )
        self.self_model.learn(
            store,
            agent_id=agent_id,
            action=action,
            supported=supported,
            progress=progress,
            effort=float(event.get("effort_signal", 0.0) or 0.0),
            sequence=frame.sequence,
        )
        self.risk.learn(
            store,
            agent_id=agent_id,
            context_signature=context,
            action=action,
            supported=supported,
            progress=progress,
            slip=float(event.get("slip_signal", 0.0) or 0.0),
            damage_signal=memory.recent_damage_signal(),
            sequence=frame.sequence,
        )
        self.causal.record_intervention(
            store,
            agent_id=agent_id,
            context_signature=context,
            action=action,
            event=event,
            sequence=frame.sequence,
        )
        self.spatial.finish_action(
            action,
            supported,
            progress,
            frame,
            store=store,
            agent_id=agent_id,
        )
        self.meta.record_outcome(
            progress=progress,
            prediction_error=prediction.error,
        )
        self._pending_context = None
        self._pending_action = None
