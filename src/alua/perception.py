from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class PerceptionFrame:
    sequence: int
    simulation_time: float
    persistent: dict[str, Any]
    target_refs: tuple[str, ...]
    appearance_ids: tuple[str, ...]


def _sanitize(value: Any, targets: list[str], appearances: list[str]) -> Any:
    if isinstance(value, dict):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if key == "target_ref":
                if isinstance(item, str):
                    targets.append(item)
                continue
            if key == "appearance_id" and isinstance(item, str):
                appearances.append(item)
            result[key] = _sanitize(item, targets, appearances)
        return result
    if isinstance(value, list):
        return [_sanitize(item, targets, appearances) for item in value]
    return value


def build_frame(observation: dict[str, Any]) -> PerceptionFrame:
    targets: list[str] = []
    appearances: list[str] = []
    persistent_channels = _sanitize(observation["channels"], targets, appearances)
    return PerceptionFrame(
        sequence=observation["sequence"],
        simulation_time=observation["simulation_time"],
        persistent={
            "schema_version": 1,
            "sequence": observation["sequence"],
            "simulation_time": observation["simulation_time"],
            "channels": persistent_channels,
        },
        target_refs=tuple(dict.fromkeys(targets)),
        appearance_ids=tuple(appearances),
    )
