from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any, Iterator

from .perception import PerceptionFrame


SCHEMA_VERSION = 1


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def strip_ephemeral(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: strip_ephemeral(item)
            for key, item in value.items()
            if key != "target_ref"
        }
    if isinstance(value, list):
        return [strip_ephemeral(item) for item in value]
    return value


class Store:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.RLock()
        self._db = sqlite3.connect(self.path, check_same_thread=False)
        self._db.row_factory = sqlite3.Row
        self._db.execute("PRAGMA journal_mode=WAL")
        self._db.execute("PRAGMA foreign_keys=ON")
        self._initialize()

    def _initialize(self) -> None:
        with self._transaction() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS meta(
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS runtime_state(
                    agent_id TEXT PRIMARY KEY,
                    session_id TEXT,
                    last_observation_sequence INTEGER NOT NULL DEFAULT 0,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS episodes(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    observation_sequence INTEGER NOT NULL,
                    simulation_time REAL NOT NULL,
                    percept_json TEXT NOT NULL,
                    created_at REAL NOT NULL,
                    UNIQUE(agent_id, session_id, observation_sequence)
                );
                CREATE TABLE IF NOT EXISTS appearance_stats(
                    agent_id TEXT NOT NULL,
                    appearance_id TEXT NOT NULL,
                    seen_count INTEGER NOT NULL,
                    first_sequence INTEGER NOT NULL,
                    last_sequence INTEGER NOT NULL,
                    PRIMARY KEY(agent_id, appearance_id)
                );
                CREATE TABLE IF NOT EXISTS decisions(
                    decision_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    observation_sequence INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    action_json TEXT NOT NULL,
                    rationale_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    request_id TEXT,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );
                CREATE TABLE IF NOT EXISTS session_events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    old_session_id TEXT,
                    new_session_id TEXT NOT NULL,
                    created_at REAL NOT NULL
                );
                """
            )
            row = db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            if row is None:
                db.execute("INSERT INTO meta(key,value) VALUES('schema_version',?)", (str(SCHEMA_VERSION),))
            elif int(row["value"]) != SCHEMA_VERSION:
                raise RuntimeError("Nepodporovaná verze Alua SQLite schématu")

    @contextmanager
    def _transaction(self) -> Iterator[sqlite3.Connection]:
        with self._lock:
            try:
                self._db.execute("BEGIN IMMEDIATE")
                yield self._db
                self._db.commit()
            except Exception:
                self._db.rollback()
                raise

    def close(self) -> None:
        with self._lock:
            self._db.close()

    def ensure_agent(self, agent_id: str) -> None:
        now = time.time()
        with self._transaction() as db:
            db.execute(
                "INSERT OR IGNORE INTO runtime_state(agent_id,updated_at) VALUES(?,?)",
                (agent_id, now),
            )

    def state(self, agent_id: str) -> dict[str, Any]:
        self.ensure_agent(agent_id)
        with self._lock:
            row = self._db.execute("SELECT * FROM runtime_state WHERE agent_id=?", (agent_id,)).fetchone()
        return dict(row)

    def apply_session(self, agent_id: str, session_id: str) -> bool:
        self.ensure_agent(agent_id)
        now = time.time()
        with self._transaction() as db:
            row = db.execute("SELECT session_id FROM runtime_state WHERE agent_id=?", (agent_id,)).fetchone()
            old = row["session_id"]
            changed = old != session_id
            if changed:
                db.execute(
                    "UPDATE runtime_state SET session_id=?,last_observation_sequence=0,updated_at=? WHERE agent_id=?",
                    (session_id, now, agent_id),
                )
                db.execute(
                    "INSERT INTO session_events(agent_id,old_session_id,new_session_id,created_at) VALUES(?,?,?,?)",
                    (agent_id, old, session_id, now),
                )
            else:
                db.execute("UPDATE runtime_state SET updated_at=? WHERE agent_id=?", (now, agent_id))
        return changed

    def seen_appearance_ids(self, agent_id: str, appearance_ids: tuple[str, ...]) -> set[str]:
        unique = sorted(set(appearance_ids))
        if not unique:
            return set()
        placeholders = ",".join("?" for _ in unique)
        with self._lock:
            rows = self._db.execute(
                f"SELECT appearance_id FROM appearance_stats WHERE agent_id=? AND appearance_id IN ({placeholders})",
                (agent_id, *unique),
            ).fetchall()
        return {row["appearance_id"] for row in rows}

    def record_observation(self, agent_id: str, session_id: str, frame: PerceptionFrame) -> bool:
        now = time.time()
        payload = canonical_json(strip_ephemeral(frame.persistent))
        with self._transaction() as db:
            existing = db.execute(
                "SELECT 1 FROM episodes WHERE agent_id=? AND session_id=? AND observation_sequence=?",
                (agent_id, session_id, frame.sequence),
            ).fetchone()
            if existing:
                return False
            db.execute(
                "INSERT INTO episodes(agent_id,session_id,observation_sequence,simulation_time,percept_json,created_at) "
                "VALUES(?,?,?,?,?,?)",
                (agent_id, session_id, frame.sequence, frame.simulation_time, payload, now),
            )
            for appearance_id in frame.appearance_ids:
                row = db.execute(
                    "SELECT seen_count FROM appearance_stats WHERE agent_id=? AND appearance_id=?",
                    (agent_id, appearance_id),
                ).fetchone()
                if row is None:
                    db.execute(
                        "INSERT INTO appearance_stats(agent_id,appearance_id,seen_count,first_sequence,last_sequence) "
                        "VALUES(?,?,?,?,?)",
                        (agent_id, appearance_id, 1, frame.sequence, frame.sequence),
                    )
                else:
                    db.execute(
                        "UPDATE appearance_stats SET seen_count=seen_count+1,last_sequence=? "
                        "WHERE agent_id=? AND appearance_id=?",
                        (frame.sequence, agent_id, appearance_id),
                    )
            db.execute(
                "UPDATE runtime_state SET last_observation_sequence=?,updated_at=? WHERE agent_id=?",
                (frame.sequence, now, agent_id),
            )
        return True

    def decision(self, decision_id: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.execute("SELECT * FROM decisions WHERE decision_id=?", (decision_id,)).fetchone()
        return dict(row) if row else None

    def record_decision(
        self,
        decision_id: str,
        agent_id: str,
        session_id: str,
        observation_sequence: int,
        action: dict[str, Any],
        rationale: dict[str, Any],
    ) -> None:
        now = time.time()
        persistent_action = strip_ephemeral(action)
        persistent_rationale = strip_ephemeral(rationale)
        with self._transaction() as db:
            db.execute(
                "INSERT OR IGNORE INTO decisions("
                "decision_id,agent_id,session_id,observation_sequence,action_type,action_json,rationale_json,status,created_at,updated_at"
                ") VALUES(?,?,?,?,?,?,?,'planned',?,?)",
                (
                    decision_id,
                    agent_id,
                    session_id,
                    observation_sequence,
                    action["type"],
                    canonical_json(persistent_action),
                    canonical_json(persistent_rationale),
                    now,
                    now,
                ),
            )

    def mark_decision_submitted(self, decision_id: str, request_id: str, status: str) -> None:
        with self._transaction() as db:
            db.execute(
                "UPDATE decisions SET request_id=?,status=?,updated_at=? WHERE decision_id=?",
                (request_id, status, time.time(), decision_id),
            )

    def summary(self, agent_id: str) -> dict[str, Any]:
        state = self.state(agent_id)
        with self._lock:
            episodes = self._db.execute("SELECT COUNT(*) FROM episodes WHERE agent_id=?", (agent_id,)).fetchone()[0]
            appearances = self._db.execute(
                "SELECT COUNT(*) FROM appearance_stats WHERE agent_id=?", (agent_id,)
            ).fetchone()[0]
            decisions = self._db.execute("SELECT COUNT(*) FROM decisions WHERE agent_id=?", (agent_id,)).fetchone()[0]
        return {
            "agent_id": agent_id,
            "session_id": state["session_id"],
            "last_observation_sequence": state["last_observation_sequence"],
            "episodes": int(episodes),
            "known_appearance_signatures": int(appearances),
            "decisions": int(decisions),
        }
