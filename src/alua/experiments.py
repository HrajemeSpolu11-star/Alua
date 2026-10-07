from __future__ import annotations

from dataclasses import dataclass

from .attention import AttentionState
from .perception import PerceptionFrame, TargetPercept
from .store import Store


@dataclass(frozen=True, slots=True)
class ExperimentProposal:
    kind: str
    target_ref: str
    target_signature: str
    information_value: float
    reason: str


class ExperimentPlanner:
    """Chooses low-risk interventions that can reduce uncertainty."""

    @staticmethod
    def _target(
        frame: PerceptionFrame,
        attention: AttentionState,
    ) -> TargetPercept | None:
        if attention.focus_signature:
            for target in frame.targets:
                if (
                    target.appearance_id == attention.focus_signature
                    and target.target_ref
                ):
                    return target
        candidates = [
            item
            for item in frame.targets
            if item.target_ref and item.appearance_id
        ]
        if not candidates:
            return None
        return min(
            candidates,
            key=lambda item: (
                item.distance_fraction
                if item.distance_fraction is not None
                else 1.0,
                item.ray_index,
            ),
        )

    def propose(
        self,
        frame: PerceptionFrame,
        attention: AttentionState,
        store: Store,
        *,
        agent_id: str,
    ) -> ExperimentProposal | None:
        target = self._target(frame, attention)
        if target is None or not target.target_ref or not target.appearance_id:
            return None
        if target.distance_fraction is None or target.distance_fraction > 0.12:
            return None

        touch = store.belief(
            agent_id,
            f"appearance:{target.appearance_id}:touch:effect",
        )
        if touch is not None:
            evidence = int(touch.get("support_count", 0)) + int(
                touch.get("contradiction_count", 0)
            )
            if evidence >= 2:
                return None

        information_value = min(
            1.0,
            0.45
            + 0.35 * attention.salience
            + 0.20 * attention.uncertainty,
        )
        return ExperimentProposal(
            kind="touch",
            target_ref=target.target_ref,
            target_signature=target.appearance_id,
            information_value=information_value,
            reason="resolve_unknown_touch_affordance",
        )
