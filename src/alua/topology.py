from __future__ import annotations

from collections import deque
import hashlib
import json
from typing import Any

from .navigation import LocalNavigator
from .perception import PerceptionFrame
from .store import Store


def _bucket(value: Any, steps: int = 5) -> int | None:
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return None
    clipped = max(0.0, min(1.0, float(value)))
    return min(steps - 1, int(clipped * steps))


def perceptual_place_signature(frame: PerceptionFrame) -> str:
    """Create an orientation-tolerant place signature from sensory evidence.

    It is a recognition key for a perceptual context, not a physical object or
    guaranteed unique world location. No target_ref or hidden map coordinates
    participate.
    """
    visual: list[tuple[Any, ...]] = []
    for target in frame.targets:
        visual.append(
            (
                target.appearance_id or "_",
                _bucket(target.distance_fraction),
                target.blocks_motion,
                target.liquid,
            )
        )
    visual.sort(key=lambda item: tuple("" if value is None else str(value) for value in item))

    channels = frame.persistent.get("channels", {})
    contact = channels.get("contact", {}) if isinstance(channels, dict) else {}
    hearing = channels.get("hearing", {}) if isinstance(channels, dict) else {}
    heard: list[tuple[str, int | None]] = []
    if isinstance(hearing, dict):
        events = hearing.get("events")
        if isinstance(events, list):
            for event in events:
                if not isinstance(event, dict):
                    continue
                signature = event.get("signature_id")
                if isinstance(signature, str):
                    heard.append((signature, _bucket(event.get("intensity"))))
    heard.sort()

    payload = {
        "visual": visual,
        "contact": {
            "supported": contact.get("supported") if isinstance(contact, dict) else None,
            "feet_in_liquid": contact.get("feet_in_liquid") if isinstance(contact, dict) else None,
            "head_submerged": contact.get("head_submerged") if isinstance(contact, dict) else None,
        },
        "heard": heard[:8],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "place-" + hashlib.sha256(encoded).hexdigest()[:24]


class PerceptualTopology:
    """Persistent transition memory over self-recognized perceptual contexts."""

    def __init__(self, history_capacity: int = 16) -> None:
        self.current_signature: str | None = None
        self._recent: deque[str] = deque(maxlen=max(4, history_capacity))
        self._pending_origin: str | None = None
        self._pending_maneuver: str | None = None

    def reset_session(self) -> None:
        self.current_signature = None
        self._recent.clear()
        self._pending_origin = None
        self._pending_maneuver = None

    def observe(
        self,
        store: Store,
        agent_id: str,
        frame: PerceptionFrame,
    ) -> str:
        signature = perceptual_place_signature(frame)
        store.record_perceptual_place(agent_id, signature, frame.sequence)
        self.current_signature = signature
        self._recent.append(signature)
        return signature

    def begin_action(self, action: dict[str, Any]) -> None:
        if action.get("type") != "move" or self.current_signature is None:
            self._pending_origin = None
            self._pending_maneuver = None
            return
        parameters = action.get("parameters")
        if not isinstance(parameters, dict):
            return
        self._pending_origin = self.current_signature
        self._pending_maneuver = LocalNavigator.maneuver_from_parameters(parameters)

    def finish_action(
        self,
        store: Store,
        agent_id: str,
        action: dict[str, Any],
        supported: bool,
        frame: PerceptionFrame,
    ) -> None:
        if action.get("type") != "move":
            return
        origin = self._pending_origin
        maneuver = self._pending_maneuver
        self._pending_origin = None
        self._pending_maneuver = None
        if origin is None or maneuver is None:
            return
        destination = perceptual_place_signature(frame)
        store.update_perceptual_transition(
            agent_id=agent_id,
            from_signature=origin,
            maneuver=maneuver,
            to_signature=destination,
            supported=supported,
            sequence=frame.sequence,
        )

    def persistent_penalties(
        self,
        store: Store,
        agent_id: str,
    ) -> dict[str, float]:
        signature = self.current_signature
        if signature is None:
            return {}
        result: dict[str, float] = {}
        for maneuver in ("forward", "left", "right", "back"):
            stats = store.perceptual_transition_stats(agent_id, signature, maneuver)
            if not stats:
                continue
            successes = int(stats["successes"])
            failures = int(stats["failures"])
            total = successes + failures
            success_rate = (successes + 1) / (total + 2)
            self_loop_rate = (
                float(stats["self_loop_successes"]) / max(1, successes)
                if successes
                else 0.0
            )
            # Failed moves are expensive. A move that physically succeeds but
            # repeatedly leaves the same perceptual context gets a smaller
            # exploration penalty because it may represent pacing in place.
            penalty = max(0.0, 0.55 - success_rate) * 1.20
            penalty += min(0.35, self_loop_rate * 0.25)
            result[maneuver] = min(1.25, penalty)
        return result

    def recent_revisit_ratio(self) -> float:
        if not self._recent:
            return 0.0
        unique = len(set(self._recent))
        return 1.0 - unique / len(self._recent)
