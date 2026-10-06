from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any, Iterator

from .perception import PerceptionFrame


SCHEMA_VERSION = 2


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
        self.last_backup_path: Path | None = None
        self._initialize()

    def _current_schema_version(self, db: sqlite3.Connection) -> int:
        try:
            row = db.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
        except sqlite3.OperationalError:
            return 0
        if row is None:
            return 0
        try:
            return int(row["value"])
        except (TypeError, ValueError):
            raise RuntimeError("Neplatná schema_version v Alua SQLite")

    def _backup_before_migration(self, old_version: int) -> None:
        if old_version <= 0 or old_version >= SCHEMA_VERSION:
            return
        stamp = time.strftime("%Y%m%d-%H%M%S", time.localtime())
        backup = self.path.with_name(self.path.name + f".pre-v{SCHEMA_VERSION}-{stamp}.bak")
        target = sqlite3.connect(backup)
        try:
            self._db.backup(target)
        finally:
            target.close()
        self.last_backup_path = backup

    @staticmethod
    def _has_column(db: sqlite3.Connection, table: str, column: str) -> bool:
        return any(row[1] == column for row in db.execute(f"PRAGMA table_info({table})").fetchall())

    def _initialize(self) -> None:
        with self._lock:
            self._db.execute(
                "CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT NOT NULL)"
            )
            self._db.commit()
            old_version = self._current_schema_version(self._db)
            if old_version > SCHEMA_VERSION:
                raise RuntimeError("Databáze byla vytvořena novější verzí Alua")
            self._backup_before_migration(old_version)

        with self._transaction() as db:
            db.executescript(
                """
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

            if not self._has_column(db, "decisions", "bridge_action_sequence"):
                db.execute("ALTER TABLE decisions ADD COLUMN bridge_action_sequence INTEGER")

            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS expectations(
                    decision_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    bridge_action_sequence INTEGER NOT NULL,
                    action_type TEXT NOT NULL,
                    target_signature TEXT,
                    action_json TEXT NOT NULL,
                    created_sequence INTEGER NOT NULL,
                    state TEXT NOT NULL,
                    outcome_json TEXT,
                    resolved_sequence INTEGER,
                    created_at REAL NOT NULL,
                    resolved_at REAL,
                    UNIQUE(agent_id, session_id, bridge_action_sequence),
                    FOREIGN KEY(decision_id) REFERENCES decisions(decision_id)
                );
                CREATE TABLE IF NOT EXISTS beliefs(
                    agent_id TEXT NOT NULL,
                    belief_key TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    subject_signature TEXT,
                    relation TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    support_count INTEGER NOT NULL,
                    contradiction_count INTEGER NOT NULL,
                    last_sequence INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(agent_id, belief_key)
                );
                """
            )
            db.execute(
                "INSERT INTO meta(key,value) VALUES('schema_version',?) "
                "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                (str(SCHEMA_VERSION),),
            )

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
                db.execute(
                    "UPDATE decisions SET status='invalidated_session',updated_at=? "
                    "WHERE agent_id=? AND session_id<>? AND status IN ('planned','queued','leased')",
                    (now, agent_id, session_id),
                )
                db.execute(
                    "UPDATE expectations SET state='invalidated_session',resolved_at=? "
                    "WHERE agent_id=? AND session_id<>? AND state='pending'",
                    (now, agent_id, session_id),
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

    def mark_decision_submitted(
        self,
        decision_id: str,
        request_id: str,
        status: str,
        bridge_action_sequence: int,
    ) -> None:
        with self._transaction() as db:
            db.execute(
                "UPDATE decisions SET request_id=?,status=?,bridge_action_sequence=?,updated_at=? WHERE decision_id=?",
                (request_id, status, int(bridge_action_sequence), time.time(), decision_id),
            )

    def record_expectation(
        self,
        *,
        decision_id: str,
        agent_id: str,
        session_id: str,
        bridge_action_sequence: int,
        action_type: str,
        target_signature: str | None,
        action: dict[str, Any],
        created_sequence: int,
    ) -> None:
        now = time.time()
        with self._transaction() as db:
            db.execute(
                "INSERT OR REPLACE INTO expectations("
                "decision_id,agent_id,session_id,bridge_action_sequence,action_type,target_signature,"
                "action_json,created_sequence,state,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,'pending',?)",
                (
                    decision_id,
                    agent_id,
                    session_id,
                    int(bridge_action_sequence),
                    action_type,
                    target_signature,
                    canonical_json(strip_ephemeral(action)),
                    int(created_sequence),
                    now,
                ),
            )

    def pending_expectation_count(self, agent_id: str, session_id: str) -> int:
        with self._lock:
            return int(
                self._db.execute(
                    "SELECT COUNT(*) FROM expectations WHERE agent_id=? AND session_id=? AND state='pending'",
                    (agent_id, session_id),
                ).fetchone()[0]
            )

    def resolve_expectation(
        self,
        *,
        agent_id: str,
        session_id: str,
        bridge_action_sequence: int,
        outcome: dict[str, Any],
        resolved_sequence: int,
    ) -> dict[str, Any] | None:
        now = time.time()
        with self._transaction() as db:
            row = db.execute(
                "SELECT * FROM expectations WHERE agent_id=? AND session_id=? "
                "AND bridge_action_sequence=? AND state='pending'",
                (agent_id, session_id, int(bridge_action_sequence)),
            ).fetchone()
            if row is None:
                return None
            db.execute(
                "UPDATE expectations SET state='resolved',outcome_json=?,resolved_sequence=?,resolved_at=? "
                "WHERE decision_id=?",
                (
                    canonical_json(strip_ephemeral(outcome)),
                    int(resolved_sequence),
                    now,
                    row["decision_id"],
                ),
            )
            result = dict(row)
            result["action"] = json.loads(result.pop("action_json"))
            return result

    def expire_old_expectations(
        self,
        agent_id: str,
        session_id: str,
        current_sequence: int,
        max_age_sequences: int = 12,
    ) -> int:
        threshold = int(current_sequence) - max(1, int(max_age_sequences))
        with self._transaction() as db:
            cursor = db.execute(
                "UPDATE expectations SET state='expired',resolved_at=? "
                "WHERE agent_id=? AND session_id=? AND state='pending' AND created_sequence<=?",
                (time.time(), agent_id, session_id, threshold),
            )
            return int(cursor.rowcount)

    def update_binary_belief(
        self,
        *,
        agent_id: str,
        belief_key: str,
        kind: str,
        subject_signature: str | None,
        relation: str,
        value: dict[str, Any],
        supported: bool,
        sequence: int,
    ) -> dict[str, Any]:
        now = time.time()
        with self._transaction() as db:
            row = db.execute(
                "SELECT * FROM beliefs WHERE agent_id=? AND belief_key=?",
                (agent_id, belief_key),
            ).fetchone()
            if row is None:
                support = 1 if supported else 0
                contradiction = 0 if supported else 1
                confidence = (support + 1) / (support + contradiction + 2)
                db.execute(
                    "INSERT INTO beliefs(agent_id,belief_key,kind,subject_signature,relation,value_json,"
                    "confidence,support_count,contradiction_count,last_sequence,created_at,updated_at)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        agent_id,
                        belief_key,
                        kind,
                        subject_signature,
                        relation,
                        canonical_json(value),
                        confidence,
                        support,
                        contradiction,
                        int(sequence),
                        now,
                        now,
                    ),
                )
            else:
                support = int(row["support_count"]) + (1 if supported else 0)
                contradiction = int(row["contradiction_count"]) + (0 if supported else 1)
                confidence = (support + 1) / (support + contradiction + 2)
                db.execute(
                    "UPDATE beliefs SET kind=?,subject_signature=?,relation=?,value_json=?,confidence=?,"
                    "support_count=?,contradiction_count=?,last_sequence=?,updated_at=? "
                    "WHERE agent_id=? AND belief_key=?",
                    (
                        kind,
                        subject_signature,
                        relation,
                        canonical_json(value),
                        confidence,
                        support,
                        contradiction,
                        int(sequence),
                        now,
                        agent_id,
                        belief_key,
                    ),
                )
        return self.belief(agent_id, belief_key) or {}

    def belief(self, agent_id: str, belief_key: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM beliefs WHERE agent_id=? AND belief_key=?",
                (agent_id, belief_key),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["value"] = json.loads(result.pop("value_json"))
        return result

    def summary(self, agent_id: str) -> dict[str, Any]:
        state = self.state(agent_id)
        with self._lock:
            episodes = self._db.execute("SELECT COUNT(*) FROM episodes WHERE agent_id=?", (agent_id,)).fetchone()[0]
            appearances = self._db.execute(
                "SELECT COUNT(*) FROM appearance_stats WHERE agent_id=?", (agent_id,)
            ).fetchone()[0]
            decisions = self._db.execute("SELECT COUNT(*) FROM decisions WHERE agent_id=?", (agent_id,)).fetchone()[0]
            beliefs = self._db.execute("SELECT COUNT(*) FROM beliefs WHERE agent_id=?", (agent_id,)).fetchone()[0]
            pending = self._db.execute(
                "SELECT COUNT(*) FROM expectations WHERE agent_id=? AND state='pending'", (agent_id,)
            ).fetchone()[0]
        return {
            "agent_id": agent_id,
            "session_id": state["session_id"],
            "last_observation_sequence": state["last_observation_sequence"],
            "episodes": int(episodes),
            "known_appearance_signatures": int(appearances),
            "decisions": int(decisions),
            "beliefs": int(beliefs),
            "pending_expectations": int(pending),
            "schema_version": SCHEMA_VERSION,
        }
