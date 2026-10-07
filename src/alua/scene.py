from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from typing import Any

from .embodiment import vital_signals
from .perception import PerceptionFrame


@dataclass(frozen=True, slots=True)
class SceneState:
    signature: str
    visual_targets: int
    auditory_events: int
    supported: bool | None
    feet_in_liquid: bool | None
    head_submerged: bool | None
    body_pressure: float


class SceneIntegrator:
    """Fuses current modalities into one bounded sensory scene."""

    @staticmethod
    def integrate(frame: PerceptionFrame) -> SceneState:
        channels = frame.persistent.get("channels")
        channels = channels if isinstance(channels, dict) else {}
        hearing = channels.get("hearing")
        contact = channels.get("contact")
        hearing = hearing if isinstance(hearing, dict) else {}
        contact = contact if isinstance(contact, dict) else {}
        events = hearing.get("events")
        auditory_events = len(events) if isinstance(events, list) else 0
        vitals = vital_signals(frame)
        pressure = max(
            1.0 - vitals.health,
            1.0 - vitals.stamina,
            vitals.hunger,
            vitals.thirst,
            vitals.fatigue,
            1.0 - vitals.breath,
        )
        visual = sorted(
            (
                target.appearance_id or "_",
                target.ray_index,
                None
                if target.distance_fraction is None
                else int(max(0.0, min(1.0, target.distance_fraction)) * 5),
                target.blocks_motion,
                target.liquid,
            )
            for target in frame.targets
        )
        heard = []
        if isinstance(events, list):
            for event in events[:8]:
                if not isinstance(event, dict):
                    continue
                heard.append(
                    (
                        event.get("signature_id"),
                        event.get("direction_bucket"),
                    )
                )
        payload = {
            "visual": visual,
            "heard": heard,
            "supported": contact.get("supported"),
            "feet_in_liquid": contact.get("feet_in_liquid"),
            "head_submerged": contact.get("head_submerged"),
            "body_pressure_bucket": int(pressure * 5),
        }
        encoded = json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode()
        signature = "scene-" + hashlib.sha256(encoded).hexdigest()[:20]
        return SceneState(
            signature=signature,
            visual_targets=len(frame.targets),
            auditory_events=auditory_events,
            supported=contact.get("supported")
            if isinstance(contact.get("supported"), bool)
            else None,
            feet_in_liquid=contact.get("feet_in_liquid")
            if isinstance(contact.get("feet_in_liquid"), bool)
            else None,
            head_submerged=contact.get("head_submerged")
            if isinstance(contact.get("head_submerged"), bool)
            else None,
            body_pressure=pressure,
        )
