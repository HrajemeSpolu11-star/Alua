from __future__ import annotations

from dataclasses import dataclass

from .attention import AttentionState
from .embodiment import vital_signals
from .memory import WorkingMemory
from .metacognition import MetaState
from .perception import PerceptionFrame


@dataclass(frozen=True, slots=True)
class DriveState:
    safety: float
    homeostasis: float
    curiosity: float
    frustration: float
    exploration: float


class DriveSystem:
    """Functional regulatory drives used only to prioritize cognition."""

    def assess(
        self,
        frame: PerceptionFrame,
        memory: WorkingMemory,
        attention: AttentionState,
        meta: MetaState,
    ) -> DriveState:
        vitals = vital_signals(frame)
        safety = max(
            memory.recent_damage_signal(),
            1.0 - vitals.health,
            1.0 - vitals.breath,
        )
        homeostasis = max(
            1.0 - vitals.stamina,
            vitals.hunger,
            vitals.thirst,
            vitals.fatigue,
        )
        curiosity = min(
            1.0,
            0.55 * attention.salience
            + 0.30 * attention.surprise
            + 0.15 * attention.uncertainty,
        )
        frustration = min(
            1.0,
            0.62 * meta.stagnation + 0.38 * meta.loop_risk,
        )
        exploration = max(
            0.0,
            min(
                1.0,
                0.55 * curiosity
                + 0.35 * (1.0 - homeostasis)
                - 0.40 * safety
                - 0.25 * frustration,
            ),
        )
        return DriveState(
            safety=max(0.0, min(1.0, safety)),
            homeostasis=max(0.0, min(1.0, homeostasis)),
            curiosity=curiosity,
            frustration=frustration,
            exploration=exploration,
        )
