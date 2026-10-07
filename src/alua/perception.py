from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TargetPercept:
    target_ref: str | None
    appearance_id: str | None
    distance_fraction: float | None
    blocks_motion: bool | None
    liquid: bool | None
    ray_index: int


@dataclass(frozen=True, slots=True)
class PerceptionFrame:
    sequence: int
    simulation_time: float
    persistent: dict[str, Any]
    targets: tuple[TargetPercept, ...]
    appearance_ids: tuple[str, ...]
    motor_events: tuple[dict[str, Any], ...]

    @property
    def target_refs(self) -> tuple[str, ...]:
        return tuple(
            target.target_ref
            for target in self.targets
            if target.target_ref is not None
        )


def _sanitize(value: Any, appearances: list[str]) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key == "target_ref":
                continue
            if key == "appearance_id" and isinstance(item, str):
                appearances.append(item)
            result[key] = _sanitize(item, appearances)
        return result
    if isinstance(value, list):
        return [_sanitize(item, appearances) for item in value]
    return value


def _number(value: Any) -> float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _targets(channels: dict[str, Any]) -> tuple[TargetPercept, ...]:
    vision = channels.get("vision")
    if not isinstance(vision, dict):
        return ()
    rays = vision.get("rays")
    if not isinstance(rays, list):
        return ()
    result: list[TargetPercept] = []
    for index, ray in enumerate(rays):
        if not isinstance(ray, dict):
            continue
        target_ref = ray.get("target_ref")
        if not isinstance(target_ref, str) or not target_ref:
            target_ref = None
        appearance_id = ray.get("appearance_id")
        if not isinstance(appearance_id, str) or not appearance_id:
            appearance_id = None
        distance = _number(ray.get("distance_fraction"))
        blocks_motion = ray.get("blocks_motion") if isinstance(ray.get("blocks_motion"), bool) else None
        liquid = ray.get("liquid") if isinstance(ray.get("liquid"), bool) else None

        # target_ref je pouze krátkodobý motorický handle. Jeho expirace nesmí
        # smazat samotný zrakový vjem; distance/appearance/blocks_motion zůstávají
        # použitelné pro navigaci a učení.
        if (
            target_ref is None
            and appearance_id is None
            and distance is None
            and blocks_motion is None
            and liquid is None
        ):
            continue

        result.append(
            TargetPercept(
                target_ref=target_ref,
                appearance_id=appearance_id,
                distance_fraction=distance,
                blocks_motion=blocks_motion,
                liquid=liquid,
                ray_index=index,
            )
        )
    return tuple(result)


def _motor_events(channels: dict[str, Any]) -> tuple[dict[str, Any], ...]:
    motor = channels.get("motor")
    if not isinstance(motor, dict) or not isinstance(motor.get("events"), list):
        return ()
    result: list[dict[str, Any]] = []
    for event in motor["events"]:
        if not isinstance(event, dict):
            continue
        source_sequence = event.get("source_sequence")
        if not isinstance(source_sequence, int) or isinstance(source_sequence, bool) or source_sequence < 1:
            continue
        result.append(
            {
                "source_sequence": source_sequence,
                "success_signal": _number(event.get("success_signal")) or 0.0,
                "progress_signal": _number(event.get("progress_signal"))
                if _number(event.get("progress_signal")) is not None
                else (_number(event.get("success_signal")) or 0.0),
                "slip_signal": _number(event.get("slip_signal")) or 0.0,
                "feedback_signal": event.get("feedback_signal")
                if isinstance(event.get("feedback_signal"), str)
                else "no_effect",
                "effort_signal": _number(event.get("effort_signal")) or 0.0,
                "age_fraction": _number(event.get("age_fraction")) or 0.0,
            }
        )
    return tuple(result)


def build_frame(observation: dict[str, Any]) -> PerceptionFrame:
    channels = observation["channels"]
    appearances: list[str] = []
    persistent_channels = _sanitize(channels, appearances)
    return PerceptionFrame(
        sequence=observation["sequence"],
        simulation_time=observation["simulation_time"],
        persistent={
            "schema_version": 1,
            "sequence": observation["sequence"],
            "simulation_time": observation["simulation_time"],
            "channels": persistent_channels,
        },
        targets=_targets(channels),
        appearance_ids=tuple(appearances),
        motor_events=_motor_events(channels),
    )
