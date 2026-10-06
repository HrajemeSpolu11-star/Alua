from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .perception import PerceptionFrame


@dataclass(frozen=True, slots=True)
class ActionIntent:
    action_type: str
    parameters: dict[str, Any]
    duration: float | None
    target_ref: str | None
    rationale: dict[str, Any]


class BootstrapPolicy:
    """Conservative first policy.

    V1 intentionally uses only wait until the World body contract for active
    movement/look parameters is end-to-end tested. This still exercises the
    full perception -> persistence -> decision -> Bridge action loop without
    inventing body semantics.
    """

    def choose(self, frame: PerceptionFrame, novel_appearances: int) -> ActionIntent:
        return ActionIntent(
            action_type="wait",
            parameters={},
            duration=0.25,
            target_ref=None,
            rationale={
                "policy": "bootstrap_observe",
                "observation_sequence": frame.sequence,
                "novel_appearance_count": int(novel_appearances),
                "target_count": len(frame.target_refs),
            },
        )
