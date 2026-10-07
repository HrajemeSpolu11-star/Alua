from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
import sqlite3
import threading
import time
from typing import Any, Iterator

from .perception import PerceptionFrame


SCHEMA_VERSION = 4


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

            for column, definition in (
                ("bridge_action_sequence", "INTEGER"),
                ("goal_key", "TEXT"),
                ("goal_kind", "TEXT"),
                ("skill_key", "TEXT"),
            ):
                if not self._has_column(db, "decisions", column):
                    db.execute(f"ALTER TABLE decisions ADD COLUMN {column} {definition}")

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
                CREATE TABLE IF NOT EXISTS goal_stats(
                    agent_id TEXT NOT NULL,
                    goal_key TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    subject_signature TEXT,
                    priority REAL NOT NULL,
                    attempts INTEGER NOT NULL,
                    successes INTEGER NOT NULL,
                    failures INTEGER NOT NULL,
                    first_sequence INTEGER NOT NULL,
                    last_sequence INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(agent_id, goal_key)
                );
                CREATE TABLE IF NOT EXISTS skills(
                    agent_id TEXT NOT NULL,
                    skill_key TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    goal_kind TEXT NOT NULL,
                    target_signature TEXT,
                    steps_json TEXT NOT NULL,
                    success_count INTEGER NOT NULL,
                    failure_count INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    reusable INTEGER NOT NULL,
                    first_sequence INTEGER NOT NULL,
                    last_sequence INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(agent_id, skill_key)
                );
                CREATE INDEX IF NOT EXISTS idx_skills_goal
                    ON skills(agent_id, goal_kind, reusable, confidence);
                CREATE INDEX IF NOT EXISTS idx_goals_kind
                    ON goal_stats(agent_id, kind, updated_at);
                CREATE TABLE IF NOT EXISTS belief_evidence(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    agent_id TEXT NOT NULL,
                    belief_key TEXT NOT NULL,
                    session_id TEXT,
                    observation_sequence INTEGER NOT NULL,
                    decision_id TEXT,
                    supported INTEGER NOT NULL,
                    created_at REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_belief_evidence_lookup
                    ON belief_evidence(agent_id, belief_key, observation_sequence);
                CREATE TABLE IF NOT EXISTS perceptual_places(
                    agent_id TEXT NOT NULL,
                    place_signature TEXT NOT NULL,
                    visit_count INTEGER NOT NULL,
                    first_sequence INTEGER NOT NULL,
                    last_sequence INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(agent_id, place_signature)
                );
                CREATE TABLE IF NOT EXISTS perceptual_transitions(
                    agent_id TEXT NOT NULL,
                    from_signature TEXT NOT NULL,
                    maneuver TEXT NOT NULL,
                    to_signature TEXT NOT NULL,
                    success_count INTEGER NOT NULL,
                    failure_count INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    first_sequence INTEGER NOT NULL,
                    last_sequence INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY(agent_id, from_signature, maneuver, to_signature)
                );
                CREATE INDEX IF NOT EXISTS idx_perceptual_transition_origin
                    ON perceptual_transitions(agent_id, from_signature, maneuver);
                """
            )

            for column, definition in (
                ("goal_key", "TEXT"),
                ("goal_kind", "TEXT"),
                ("skill_key", "TEXT"),
            ):
                if not self._has_column(db, "expectations", column):
                    db.execute(f"ALTER TABLE expectations ADD COLUMN {column} {definition}")

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
            row = self._db.execute(
                "SELECT * FROM runtime_state WHERE agent_id=?",
                (agent_id,),
            ).fetchone()
        return dict(row)

    def apply_session(self, agent_id: str, session_id: str) -> bool:
        self.ensure_agent(agent_id)
        now = time.time()
        with self._transaction() as db:
            row = db.execute(
                "SELECT session_id FROM runtime_state WHERE agent_id=?",
                (agent_id,),
            ).fetchone()
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
                db.execute(
                    "UPDATE runtime_state SET updated_at=? WHERE agent_id=?",
                    (now, agent_id),
                )
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

    def record_observation(
        self,
        agent_id: str,
        session_id: str,
        frame: PerceptionFrame,
    ) -> bool:
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
            row = self._db.execute(
                "SELECT * FROM decisions WHERE decision_id=?",
                (decision_id,),
            ).fetchone()
        return dict(row) if row else None

    def record_decision(
        self,
        decision_id: str,
        agent_id: str,
        session_id: str,
        observation_sequence: int,
        action: dict[str, Any],
        rationale: dict[str, Any],
        *,
        goal_key: str | None = None,
        goal_kind: str | None = None,
        skill_key: str | None = None,
    ) -> None:
        now = time.time()
        persistent_action = strip_ephemeral(action)
        persistent_rationale = strip_ephemeral(rationale)
        with self._transaction() as db:
            db.execute(
                "INSERT OR IGNORE INTO decisions("
                "decision_id,agent_id,session_id,observation_sequence,action_type,action_json,"
                "rationale_json,status,goal_key,goal_kind,skill_key,created_at,updated_at"
                ") VALUES(?,?,?,?,?,?,?,'planned',?,?,?,?,?)",
                (
                    decision_id,
                    agent_id,
                    session_id,
                    observation_sequence,
                    action["type"],
                    canonical_json(persistent_action),
                    canonical_json(persistent_rationale),
                    goal_key,
                    goal_kind,
                    skill_key,
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

    def mark_decision_rejected(self, decision_id: str, status: str) -> None:
        if not status or len(status) > 64:
            raise ValueError("decision rejection status must be short")
        with self._transaction() as db:
            db.execute(
                "UPDATE decisions SET status=?,updated_at=? WHERE decision_id=?",
                (status, time.time(), decision_id),
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
        goal_key: str | None = None,
        goal_kind: str | None = None,
        skill_key: str | None = None,
    ) -> None:
        now = time.time()
        with self._transaction() as db:
            db.execute(
                "INSERT OR REPLACE INTO expectations("
                "decision_id,agent_id,session_id,bridge_action_sequence,action_type,target_signature,"
                "action_json,created_sequence,state,goal_key,goal_kind,skill_key,created_at"
                ") VALUES(?,?,?,?,?,?,?,?,'pending',?,?,?,?)",
                (
                    decision_id,
                    agent_id,
                    session_id,
                    int(bridge_action_sequence),
                    action_type,
                    target_signature,
                    canonical_json(strip_ephemeral(action)),
                    int(created_sequence),
                    goal_key,
                    goal_kind,
                    skill_key,
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
            db.execute(
                "UPDATE decisions SET status='resolved',updated_at=? WHERE decision_id=?",
                (now, row["decision_id"]),
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
        now = time.time()
        with self._transaction() as db:
            rows = db.execute(
                "SELECT decision_id FROM expectations WHERE agent_id=? AND session_id=? "
                "AND state='pending' AND created_sequence<=?",
                (agent_id, session_id, threshold),
            ).fetchall()
            if not rows:
                return 0
            ids = [row["decision_id"] for row in rows]
            db.executemany(
                "UPDATE expectations SET state='expired',resolved_at=? WHERE decision_id=?",
                [(now, decision_id) for decision_id in ids],
            )
            db.executemany(
                "UPDATE decisions SET status='expired',updated_at=? WHERE decision_id=?",
                [(now, decision_id) for decision_id in ids],
            )
            return len(ids)

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
        evidence_session_id: str | None = None,
        evidence_decision_id: str | None = None,
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

            if evidence_session_id is not None or evidence_decision_id is not None:
                db.execute(
                    "INSERT INTO belief_evidence("
                    "agent_id,belief_key,session_id,observation_sequence,decision_id,supported,created_at"
                    ") VALUES(?,?,?,?,?,?,?)",
                    (
                        agent_id,
                        belief_key,
                        evidence_session_id,
                        int(sequence),
                        evidence_decision_id,
                        1 if supported else 0,
                        now,
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

    def record_goal_attempt(
        self,
        *,
        agent_id: str,
        goal_key: str,
        kind: str,
        subject_signature: str | None,
        priority: float,
        sequence: int,
    ) -> dict[str, Any]:
        now = time.time()
        with self._transaction() as db:
            row = db.execute(
                "SELECT attempts FROM goal_stats WHERE agent_id=? AND goal_key=?",
                (agent_id, goal_key),
            ).fetchone()
            if row is None:
                db.execute(
                    "INSERT INTO goal_stats(agent_id,goal_key,kind,subject_signature,priority,"
                    "attempts,successes,failures,first_sequence,last_sequence,created_at,updated_at)"
                    " VALUES(?,?,?,?,?,1,0,0,?,?,?,?)",
                    (
                        agent_id,
                        goal_key,
                        kind,
                        subject_signature,
                        float(priority),
                        int(sequence),
                        int(sequence),
                        now,
                        now,
                    ),
                )
            else:
                db.execute(
                    "UPDATE goal_stats SET kind=?,subject_signature=?,priority=?,attempts=attempts+1,"
                    "last_sequence=?,updated_at=? WHERE agent_id=? AND goal_key=?",
                    (
                        kind,
                        subject_signature,
                        float(priority),
                        int(sequence),
                        now,
                        agent_id,
                        goal_key,
                    ),
                )
        return self.goal_stats(agent_id, goal_key) or {}

    def record_goal_outcome(
        self,
        *,
        agent_id: str,
        goal_key: str,
        kind: str,
        subject_signature: str | None,
        supported: bool,
        sequence: int,
    ) -> dict[str, Any]:
        now = time.time()
        with self._transaction() as db:
            row = db.execute(
                "SELECT 1 FROM goal_stats WHERE agent_id=? AND goal_key=?",
                (agent_id, goal_key),
            ).fetchone()
            if row is None:
                db.execute(
                    "INSERT INTO goal_stats(agent_id,goal_key,kind,subject_signature,priority,"
                    "attempts,successes,failures,first_sequence,last_sequence,created_at,updated_at)"
                    " VALUES(?,?,?,?,0,0,?,?, ?,?,?,?)",
                    (
                        agent_id,
                        goal_key,
                        kind,
                        subject_signature,
                        1 if supported else 0,
                        0 if supported else 1,
                        int(sequence),
                        int(sequence),
                        now,
                        now,
                    ),
                )
            else:
                column = "successes" if supported else "failures"
                db.execute(
                    f"UPDATE goal_stats SET {column}={column}+1,kind=?,subject_signature=?,"
                    "last_sequence=?,updated_at=? WHERE agent_id=? AND goal_key=?",
                    (
                        kind,
                        subject_signature,
                        int(sequence),
                        now,
                        agent_id,
                        goal_key,
                    ),
                )
        return self.goal_stats(agent_id, goal_key) or {}

    def goal_stats(self, agent_id: str, goal_key: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM goal_stats WHERE agent_id=? AND goal_key=?",
                (agent_id, goal_key),
            ).fetchone()
        return dict(row) if row else None

    def update_skill_evidence(
        self,
        *,
        agent_id: str,
        skill_key: str,
        kind: str,
        goal_kind: str,
        target_signature: str | None,
        steps: list[dict[str, Any]],
        supported: bool,
        sequence: int,
        min_successes: int,
        min_confidence: float,
    ) -> dict[str, Any]:
        now = time.time()
        safe_steps = strip_ephemeral(steps)
        encoded_steps = canonical_json(safe_steps)
        with self._transaction() as db:
            row = db.execute(
                "SELECT * FROM skills WHERE agent_id=? AND skill_key=?",
                (agent_id, skill_key),
            ).fetchone()
            if row is None:
                successes = 1 if supported else 0
                failures = 0 if supported else 1
                confidence = (successes + 1) / (successes + failures + 2)
                reusable = int(successes >= min_successes and confidence >= min_confidence)
                db.execute(
                    "INSERT INTO skills(agent_id,skill_key,kind,goal_kind,target_signature,steps_json,"
                    "success_count,failure_count,confidence,reusable,first_sequence,last_sequence,created_at,updated_at)"
                    " VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        agent_id,
                        skill_key,
                        kind,
                        goal_kind,
                        target_signature,
                        encoded_steps,
                        successes,
                        failures,
                        confidence,
                        reusable,
                        int(sequence),
                        int(sequence),
                        now,
                        now,
                    ),
                )
            else:
                successes = int(row["success_count"]) + (1 if supported else 0)
                failures = int(row["failure_count"]) + (0 if supported else 1)
                confidence = (successes + 1) / (successes + failures + 2)
                reusable = int(successes >= min_successes and confidence >= min_confidence)
                db.execute(
                    "UPDATE skills SET kind=?,goal_kind=?,target_signature=?,steps_json=?,"
                    "success_count=?,failure_count=?,confidence=?,reusable=?,last_sequence=?,updated_at=? "
                    "WHERE agent_id=? AND skill_key=?",
                    (
                        kind,
                        goal_kind,
                        target_signature,
                        encoded_steps,
                        successes,
                        failures,
                        confidence,
                        reusable,
                        int(sequence),
                        now,
                        agent_id,
                        skill_key,
                    ),
                )
        return self.skill(agent_id, skill_key) or {}

    def skill(self, agent_id: str, skill_key: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.execute(
                "SELECT * FROM skills WHERE agent_id=? AND skill_key=?",
                (agent_id, skill_key),
            ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["steps"] = json.loads(result.pop("steps_json"))
        result["reusable"] = bool(result["reusable"])
        return result

    def best_reusable_skill(
        self,
        *,
        agent_id: str,
        goal_kind: str,
        target_signature: str | None,
    ) -> dict[str, Any] | None:
        with self._lock:
            if target_signature is None:
                row = self._db.execute(
                    "SELECT * FROM skills WHERE agent_id=? AND goal_kind=? AND reusable=1 "
                    "AND target_signature IS NULL ORDER BY confidence DESC,success_count DESC,updated_at DESC LIMIT 1",
                    (agent_id, goal_kind),
                ).fetchone()
            else:
                row = self._db.execute(
                    "SELECT * FROM skills WHERE agent_id=? AND goal_kind=? AND reusable=1 "
                    "AND target_signature=? ORDER BY confidence DESC,success_count DESC,updated_at DESC LIMIT 1",
                    (agent_id, goal_kind, target_signature),
                ).fetchone()
        if row is None:
            return None
        result = dict(row)
        result["steps"] = json.loads(result.pop("steps_json"))
        result["reusable"] = bool(result["reusable"])
        return result

    def belief_evidence(
        self,
        agent_id: str,
        belief_key: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(1000, int(limit)))
        with self._lock:
            rows = self._db.execute(
                "SELECT agent_id,belief_key,session_id,observation_sequence,decision_id,supported,created_at "
                "FROM belief_evidence WHERE agent_id=? AND belief_key=? "
                "ORDER BY id DESC LIMIT ?",
                (agent_id, belief_key, limit),
            ).fetchall()
        result = [dict(row) for row in rows]
        for item in result:
            item["supported"] = bool(item["supported"])
        return result

    def record_perceptual_place(
        self,
        agent_id: str,
        place_signature: str,
        sequence: int,
    ) -> dict[str, Any]:
        now = time.time()
        with self._transaction() as db:
            row = db.execute(
                "SELECT visit_count FROM perceptual_places WHERE agent_id=? AND place_signature=?",
                (agent_id, place_signature),
            ).fetchone()
            if row is None:
                db.execute(
                    "INSERT INTO perceptual_places("
                    "agent_id,place_signature,visit_count,first_sequence,last_sequence,created_at,updated_at"
                    ") VALUES(?,?,1,?,?,?,?)",
                    (agent_id, place_signature, int(sequence), int(sequence), now, now),
                )
            else:
                db.execute(
                    "UPDATE perceptual_places SET visit_count=visit_count+1,last_sequence=?,updated_at=? "
                    "WHERE agent_id=? AND place_signature=?",
                    (int(sequence), now, agent_id, place_signature),
                )
        with self._lock:
            result = self._db.execute(
                "SELECT * FROM perceptual_places WHERE agent_id=? AND place_signature=?",
                (agent_id, place_signature),
            ).fetchone()
        return dict(result) if result else {}

    def update_perceptual_transition(
        self,
        *,
        agent_id: str,
        from_signature: str,
        maneuver: str,
        to_signature: str,
        supported: bool,
        sequence: int,
    ) -> dict[str, Any]:
        if maneuver not in {"forward", "left", "right", "back"}:
            raise ValueError("unsupported maneuver")
        now = time.time()
        with self._transaction() as db:
            row = db.execute(
                "SELECT success_count,failure_count FROM perceptual_transitions "
                "WHERE agent_id=? AND from_signature=? AND maneuver=? AND to_signature=?",
                (agent_id, from_signature, maneuver, to_signature),
            ).fetchone()
            if row is None:
                successes = 1 if supported else 0
                failures = 0 if supported else 1
                confidence = (successes + 1) / (successes + failures + 2)
                db.execute(
                    "INSERT INTO perceptual_transitions("
                    "agent_id,from_signature,maneuver,to_signature,success_count,failure_count,"
                    "confidence,first_sequence,last_sequence,created_at,updated_at"
                    ") VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                    (
                        agent_id,
                        from_signature,
                        maneuver,
                        to_signature,
                        successes,
                        failures,
                        confidence,
                        int(sequence),
                        int(sequence),
                        now,
                        now,
                    ),
                )
            else:
                successes = int(row["success_count"]) + (1 if supported else 0)
                failures = int(row["failure_count"]) + (0 if supported else 1)
                confidence = (successes + 1) / (successes + failures + 2)
                db.execute(
                    "UPDATE perceptual_transitions SET success_count=?,failure_count=?,confidence=?,"
                    "last_sequence=?,updated_at=? WHERE agent_id=? AND from_signature=? AND maneuver=? AND to_signature=?",
                    (
                        successes,
                        failures,
                        confidence,
                        int(sequence),
                        now,
                        agent_id,
                        from_signature,
                        maneuver,
                        to_signature,
                    ),
                )
        with self._lock:
            result = self._db.execute(
                "SELECT * FROM perceptual_transitions WHERE agent_id=? AND from_signature=? "
                "AND maneuver=? AND to_signature=?",
                (agent_id, from_signature, maneuver, to_signature),
            ).fetchone()
        return dict(result) if result else {}

    def perceptual_transition_stats(
        self,
        agent_id: str,
        from_signature: str,
        maneuver: str,
    ) -> dict[str, Any] | None:
        with self._lock:
            row = self._db.execute(
                "SELECT COALESCE(SUM(success_count),0) AS successes,"
                "COALESCE(SUM(failure_count),0) AS failures,"
                "COALESCE(SUM(CASE WHEN to_signature=from_signature THEN success_count ELSE 0 END),0) "
                "AS self_loop_successes,"
                "COUNT(*) AS destinations "
                "FROM perceptual_transitions WHERE agent_id=? AND from_signature=? AND maneuver=?",
                (agent_id, from_signature, maneuver),
            ).fetchone()
        if row is None or int(row["successes"]) + int(row["failures"]) == 0:
            return None
        return dict(row)

    def session_episodes(
        self,
        agent_id: str,
        session_id: str | None = None,
        *,
        limit: int = 5000,
    ) -> list[dict[str, Any]]:
        limit = max(1, min(20000, int(limit)))
        if session_id is None:
            session_id = self.state(agent_id).get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return []
        with self._lock:
            rows = self._db.execute(
                "SELECT percept_json FROM episodes WHERE agent_id=? AND session_id=? "
                "ORDER BY observation_sequence DESC LIMIT ?",
                (agent_id, session_id, limit),
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in reversed(rows):
            try:
                payload = json.loads(row["percept_json"])
            except (TypeError, json.JSONDecodeError):
                continue
            if isinstance(payload, dict):
                result.append(payload)
        return result

    def session_trace(
        self,
        agent_id: str,
        session_id: str | None = None,
        *,
        limit: int = 500,
    ) -> list[dict[str, Any]]:
        """Return a bounded decision/outcome trace for offline behavior evaluation."""
        limit = max(1, min(5000, int(limit)))
        if session_id is None:
            session_id = self.state(agent_id).get("session_id")
        if not isinstance(session_id, str) or not session_id:
            return []
        with self._lock:
            rows = self._db.execute(
                "SELECT d.decision_id,d.session_id,d.observation_sequence,d.action_type,"
                "d.action_json,d.rationale_json,d.status,d.goal_key,d.goal_kind,d.skill_key,"
                "d.bridge_action_sequence,e.state AS expectation_state,e.outcome_json "
                "FROM decisions d LEFT JOIN expectations e ON e.decision_id=d.decision_id "
                "WHERE d.agent_id=? AND d.session_id=? "
                "ORDER BY d.observation_sequence DESC,d.created_at DESC LIMIT ?",
                (agent_id, session_id, limit),
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in reversed(rows):
            item = dict(row)
            try:
                item["action"] = json.loads(item.pop("action_json"))
            except (TypeError, json.JSONDecodeError):
                item["action"] = {}
            try:
                item["rationale"] = json.loads(item.pop("rationale_json"))
            except (TypeError, json.JSONDecodeError):
                item["rationale"] = {}
            outcome_raw = item.pop("outcome_json", None)
            outcome = None
            if isinstance(outcome_raw, str) and outcome_raw:
                try:
                    parsed = json.loads(outcome_raw)
                    if isinstance(parsed, dict):
                        outcome = parsed
                except json.JSONDecodeError:
                    outcome = None
            item["outcome"] = outcome
            signal = outcome.get("success_signal") if isinstance(outcome, dict) else None
            feedback = outcome.get("feedback_signal") if isinstance(outcome, dict) else None
            item["outcome_success"] = (
                bool(
                    float(signal) >= 0.55
                    and feedback not in {
                        "partial_effect",
                        "no_effect",
                        "resistance",
                        "impact_resisted",
                        "containment_failed",
                    }
                )
                if isinstance(signal, (int, float)) and not isinstance(signal, bool)
                else None
            )
            progress = outcome.get("progress_signal") if isinstance(outcome, dict) else None
            item["progress_signal"] = (
                max(0.0, min(1.0, float(progress)))
                if isinstance(progress, (int, float)) and not isinstance(progress, bool)
                else None
            )
            result.append(item)
        return result

    def latest_submitted_goal(
        self,
        agent_id: str,
        session_id: str,
    ) -> dict[str, Any] | None:
        """Return the newest action that Bridge actually accepted in this session."""
        with self._lock:
            row = self._db.execute(
                "SELECT goal_key,goal_kind,action_type,bridge_action_sequence,observation_sequence,created_at "
                "FROM decisions WHERE agent_id=? AND session_id=? "
                "AND bridge_action_sequence IS NOT NULL "
                "ORDER BY bridge_action_sequence DESC LIMIT 1",
                (agent_id, session_id),
            ).fetchone()
        return dict(row) if row else None

    def deactivate_reusable_skills_outside(
        self,
        agent_id: str,
        allowed_goal_kinds: set[str] | frozenset[str],
    ) -> int:
        allowed = sorted({kind for kind in allowed_goal_kinds if isinstance(kind, str) and kind})
        if not allowed:
            return 0
        placeholders = ",".join("?" for _ in allowed)
        with self._transaction() as db:
            cursor = db.execute(
                f"UPDATE skills SET reusable=0,updated_at=? "
                f"WHERE agent_id=? AND reusable=1 AND goal_kind NOT IN ({placeholders})",
                (time.time(), agent_id, *allowed),
            )
            return max(0, int(cursor.rowcount))

    def summary(self, agent_id: str) -> dict[str, Any]:
        state = self.state(agent_id)
        with self._lock:
            episodes = self._db.execute(
                "SELECT COUNT(*) FROM episodes WHERE agent_id=?",
                (agent_id,),
            ).fetchone()[0]
            appearances = self._db.execute(
                "SELECT COUNT(*) FROM appearance_stats WHERE agent_id=?",
                (agent_id,),
            ).fetchone()[0]
            decisions = self._db.execute(
                "SELECT COUNT(*) FROM decisions WHERE agent_id=?",
                (agent_id,),
            ).fetchone()[0]
            beliefs = self._db.execute(
                "SELECT COUNT(*) FROM beliefs WHERE agent_id=?",
                (agent_id,),
            ).fetchone()[0]
            pending = self._db.execute(
                "SELECT COUNT(*) FROM expectations WHERE agent_id=? AND state='pending'",
                (agent_id,),
            ).fetchone()[0]
            goals = self._db.execute(
                "SELECT COUNT(*) FROM goal_stats WHERE agent_id=?",
                (agent_id,),
            ).fetchone()[0]
            skills = self._db.execute(
                "SELECT COUNT(*) FROM skills WHERE agent_id=?",
                (agent_id,),
            ).fetchone()[0]
            reusable = self._db.execute(
                "SELECT COUNT(*) FROM skills WHERE agent_id=? AND reusable=1",
                (agent_id,),
            ).fetchone()[0]
            belief_evidence_count = self._db.execute(
                "SELECT COUNT(*) FROM belief_evidence WHERE agent_id=?",
                (agent_id,),
            ).fetchone()[0]
            perceptual_places = self._db.execute(
                "SELECT COUNT(*) FROM perceptual_places WHERE agent_id=?",
                (agent_id,),
            ).fetchone()[0]
            perceptual_transitions = self._db.execute(
                "SELECT COUNT(*) FROM perceptual_transitions WHERE agent_id=?",
                (agent_id,),
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
            "goals": int(goals),
            "skills": int(skills),
            "reusable_skills": int(reusable),
            "belief_evidence": int(belief_evidence_count),
            "perceptual_places": int(perceptual_places),
            "perceptual_transitions": int(perceptual_transitions),
            "schema_version": SCHEMA_VERSION,
        }
