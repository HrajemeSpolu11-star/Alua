from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .perception import PerceptionFrame, TargetPercept


def _number(value: Any, default: float = 0.0) -> float:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return default


def _channels(frame: PerceptionFrame) -> dict[str, Any]:
    channels = frame.persistent.get("channels")
    return channels if isinstance(channels, dict) else {}


@dataclass(frozen=True, slots=True)
class VitalSignals:
    health: float
    stamina: float
    hunger: float
    thirst: float
    fatigue: float
    breath: float


@dataclass(frozen=True, slots=True)
class InventorySlot:
    slot_index: int
    appearance_id: str
    count: int
    mass_fraction: float


def vital_signals(frame: PerceptionFrame) -> VitalSignals:
    raw = _channels(frame).get("vitals")
    if not isinstance(raw, dict):
        raw = {}
    return VitalSignals(
        health=max(0.0, min(1.0, _number(raw.get("health_fraction"), 1.0))),
        stamina=max(0.0, min(1.0, _number(raw.get("stamina_fraction"), 1.0))),
        hunger=max(0.0, min(1.0, _number(raw.get("hunger_signal")))),
        thirst=max(0.0, min(1.0, _number(raw.get("thirst_signal")))),
        fatigue=max(0.0, min(1.0, _number(raw.get("fatigue_signal")))),
        breath=max(0.0, min(1.0, _number(raw.get("breath_fraction"), 1.0))),
    )


def inventory_slots(frame: PerceptionFrame) -> tuple[InventorySlot, ...]:
    raw = _channels(frame).get("inventory")
    if not isinstance(raw, dict) or not isinstance(raw.get("slots"), list):
        return ()
    result: list[InventorySlot] = []
    for item in raw["slots"]:
        if not isinstance(item, dict):
            continue
        index = item.get("slot_index")
        appearance = item.get("appearance_id")
        count = item.get("count")
        if (
            not isinstance(index, int)
            or isinstance(index, bool)
            or index < 1
            or not isinstance(appearance, str)
            or not appearance
            or not isinstance(count, int)
            or isinstance(count, bool)
            or count < 1
        ):
            continue
        result.append(
            InventorySlot(
                slot_index=index,
                appearance_id=appearance,
                count=count,
                mass_fraction=max(
                    0.0,
                    min(1.0, _number(item.get("mass_fraction"))),
                ),
            )
        )
    return tuple(sorted(result, key=lambda slot: slot.slot_index))


def inventory_load(frame: PerceptionFrame) -> float:
    raw = _channels(frame).get("inventory")
    if not isinstance(raw, dict):
        return 0.0
    return max(0.0, min(1.0, _number(raw.get("load_fraction"))))


def locomotion_signals(frame: PerceptionFrame) -> dict[str, float | str]:
    raw = _channels(frame).get("locomotion")
    if not isinstance(raw, dict):
        return {}
    result: dict[str, float | str] = {}
    for key in (
        "grounded_signal",
        "front_feet_blocked_signal",
        "front_torso_blocked_signal",
        "front_head_blocked_signal",
        "overhead_blocked_signal",
        "step_up_signal",
        "crouch_clearance_signal",
        "crawl_clearance_signal",
        "gap_ahead_signal",
        "jump_gap_signal",
        "drop_depth_signal",
        "safe_drop_signal",
        "climbable_signal",
        "feet_in_liquid_signal",
        "head_submerged_signal",
    ):
        result[key] = max(0.0, min(1.0, _number(raw.get(key))))
    for key in ("posture", "active_mode"):
        if isinstance(raw.get(key), str):
            result[key] = raw[key]
    return result


def nearest_target(
    frame: PerceptionFrame,
    *,
    require_ref: bool = True,
    liquid: bool | None = None,
) -> TargetPercept | None:
    candidates = []
    for target in frame.targets:
        if require_ref and not target.target_ref:
            continue
        if liquid is not None and target.liquid is not liquid:
            continue
        if target.distance_fraction is None:
            continue
        candidates.append(target)
    if not candidates:
        return None
    return min(
        candidates,
        key=lambda target: (
            target.distance_fraction if target.distance_fraction is not None else 1.0,
            target.ray_index,
        ),
    )


def inventory_slot_by_appearance(
    frame: PerceptionFrame,
    appearance_id: str,
) -> InventorySlot | None:
    return next(
        (slot for slot in inventory_slots(frame) if slot.appearance_id == appearance_id),
        None,
    )
