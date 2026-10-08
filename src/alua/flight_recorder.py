"""Operator-only Cognitive V5 flight recorder.

This reads *existing* evidence persisted by Alua; never contacts World or
Bridge and never injects cognition, invented outcomes or privileged data.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any, TextIO

from .store import Store


def snapshot(store: Store, agent_id: str, limit: int, include_episodes: bool) -> list[dict[str, Any]]:
    state = store.state(agent_id)
    session = state.get("session_id")
    if not session:
        return [{"event": "no_session", "agent_id": agent_id}]
    result: list[dict[str, Any]] = []
    if include_episodes:
        for episode in store.session_episodes(agent_id, session, limit=limit):
            seq = episode.get("sequence", episode.get("observation_sequence"))
            result.append({
                "event": "sensory_episode",
                "agent_id": agent_id,
                "session_id": session,
                "observation_sequence": seq,
                "perception": episode,
            })
    for decision in store.session_trace(agent_id, session, limit=limit):
        result.append({
            "event": "cognitive_decision",
            "agent_id": agent_id,
            "session_id": session,
            "observation_sequence": decision.get("observation_sequence"),
            "decision_id": decision.get("decision_id"),
            "goal": {"key": decision.get("goal_key"), "kind": decision.get("goal_kind")},
            "skill_key": decision.get("skill_key"),
            "decision_status": decision.get("status"),
            "action": decision.get("action"),
            "rationale": decision.get("rationale"),
            "cognitive_state": (decision.get("rationale") or {}).get("cognitive_state"),
            "bridge_action_sequence": decision.get("bridge_action_sequence"),
            "expectation_state": decision.get("expectation_state"),
            "verified_motor_outcome": decision.get("outcome"),
            "outcome_success": decision.get("outcome_success"),
            "progress_signal": decision.get("progress_signal"),
        })
    last = store.cognitive_record(agent_id, "cognition:last-state")
    if last is not None:
        result.append({
            "event": "cognitive_model_snapshot",
            "agent_id": agent_id,
            "session_id": session,
            "model": last.get("payload"),
            "model_updated_at": last.get("updated_at"),
        })
    return result


def output_lines(store: Store, agent_id: str, limit: int, include_episodes: bool,
                 output: TextIO, follow: bool = False, interval: float = 2.0) -> None:
    seen: dict[tuple[str, str, str], str] = {}
    active_session = None
    while True:
        rows = snapshot(store, agent_id, limit, include_episodes)
        session = rows[0].get("session_id") if rows else None
        if session != active_session:
            seen.clear()
            active_session = session
        for row in rows:
            kind = row["event"]
            key = (str(row.get("session_id")), kind,
                   str(row.get("decision_id") or row.get("observation_sequence")
                       or row.get("model_updated_at") or "state"))
            serialized = json.dumps(row, ensure_ascii=False, sort_keys=True,
                                    separators=(",", ":"), allow_nan=False)
            if seen.get(key) == serialized:
                continue
            seen[key] = serialized
            output.write(serialized + "\n")
        output.flush()
        if not follow:
            return
        # Bounded in-memory deduplication across long-running recordings.
        if len(seen) > 3 * max(1, limit) + 10:
            seen = dict(list(seen.items())[-(2 * limit + 10):])
        time.sleep(interval)


def secure_log_file(path: str) -> TextIO:
    """Append operator evidence without making it group/world-readable."""
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(target), os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    os.chmod(target, 0o600)
    return os.fdopen(fd, "a", encoding="utf-8")
