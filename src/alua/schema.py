from __future__ import annotations

from typing import Any

from .errors import ProtocolError


FORBIDDEN_WORLD_KEYS = {
    "node_name",
    "item_name",
    "material",
    "biome",
    "catalog_id",
    "internal_id",
    "world_truth",
    "lua_object",
    "objectref",
    "absolute_position",
}


def _require_object(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ProtocolError(f"{label} musí být JSON objekt")
    return value


def _reject_forbidden(value: Any) -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            if key in FORBIDDEN_WORLD_KEYS:
                raise ProtocolError(f"Observation obsahuje zakázaný world-truth klíč: {key}")
            _reject_forbidden(item)
    elif isinstance(value, list):
        for item in value:
            _reject_forbidden(item)


def validate_session(value: Any, expected_agent_id: str) -> dict[str, Any]:
    body = _require_object(value, "session")
    allowed = {
        "schema_version",
        "agent_id",
        "session_id",
        "last_observation_sequence",
        "last_action_sequence",
    }
    extra = set(body) - allowed
    if extra:
        raise ProtocolError("Neznámá pole session: " + ", ".join(sorted(extra)))
    if body.get("schema_version") != 1:
        raise ProtocolError("Podporováno je pouze schema_version 1")
    if body.get("agent_id") != expected_agent_id:
        raise ProtocolError("Bridge vrátil jiného agent_id")
    session_id = body.get("session_id")
    if not isinstance(session_id, str) or not session_id:
        raise ProtocolError("session_id chybí")
    for key in ("last_observation_sequence", "last_action_sequence"):
        item = body.get(key)
        if not isinstance(item, int) or isinstance(item, bool) or item < 0:
            raise ProtocolError(f"{key} musí být nezáporné celé číslo")
    return {
        "schema_version": 1,
        "agent_id": expected_agent_id,
        "session_id": session_id,
        "last_observation_sequence": body["last_observation_sequence"],
        "last_action_sequence": body["last_action_sequence"],
    }


def validate_observation(value: Any, expected_agent_id: str) -> dict[str, Any]:
    body = _require_object(value, "observation")
    allowed = {"schema_version", "agent_id", "sequence", "simulation_time", "channels"}
    extra = set(body) - allowed
    if extra:
        raise ProtocolError("Neznámá pole observation: " + ", ".join(sorted(extra)))
    if body.get("schema_version") != 1:
        raise ProtocolError("Podporováno je pouze schema_version 1")
    if body.get("agent_id") != expected_agent_id:
        raise ProtocolError("Observation patří jinému agentovi")
    sequence = body.get("sequence")
    if not isinstance(sequence, int) or isinstance(sequence, bool) or sequence < 1:
        raise ProtocolError("sequence musí být kladné celé číslo")
    simulation_time = body.get("simulation_time")
    if not isinstance(simulation_time, (int, float)) or isinstance(simulation_time, bool) or simulation_time < 0:
        raise ProtocolError("simulation_time musí být nezáporné číslo")
    channels = body.get("channels")
    if not isinstance(channels, dict):
        raise ProtocolError("channels musí být objekt")
    _reject_forbidden(channels)
    return {
        "schema_version": 1,
        "agent_id": expected_agent_id,
        "sequence": sequence,
        "simulation_time": float(simulation_time),
        "channels": channels,
    }


def validate_observation_response(value: Any, expected_agent_id: str) -> list[dict[str, Any]]:
    body = _require_object(value, "observation response")
    allowed = {"schema_version", "agent_id", "observations"}
    extra = set(body) - allowed
    if extra:
        raise ProtocolError("Neznámá pole observation response: " + ", ".join(sorted(extra)))
    if body.get("schema_version") != 1 or body.get("agent_id") != expected_agent_id:
        raise ProtocolError("Observation response neodpovídá kontraktu agenta")
    observations = body.get("observations")
    if not isinstance(observations, list):
        raise ProtocolError("observations musí být pole")
    return [validate_observation(item, expected_agent_id) for item in observations]


def validate_action_response(value: Any) -> dict[str, Any]:
    body = _require_object(value, "action response")
    if body.get("ok") is not True:
        raise ProtocolError("Bridge nepotvrdil přijetí ActionRequest")
    request_id = body.get("request_id")
    sequence = body.get("action_sequence")
    status = body.get("status")
    if not isinstance(request_id, str) or not request_id:
        raise ProtocolError("action response nemá request_id")
    if not isinstance(sequence, int) or sequence < 1:
        raise ProtocolError("action response nemá platnou action_sequence")
    if not isinstance(status, str) or not status:
        raise ProtocolError("action response nemá status")
    return {
        "request_id": request_id,
        "action_sequence": sequence,
        "status": status,
        "duplicate": body.get("duplicate") is True,
    }
