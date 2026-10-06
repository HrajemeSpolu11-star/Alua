from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import logging
import time
from typing import Any

from .bridge_client import BridgeClient
from .config import Config
from .errors import BridgeHttpError, BridgeUnavailable, ProtocolError
from .perception import PerceptionFrame, build_frame
from .policy import BootstrapPolicy
from .store import Store


LOG = logging.getLogger("alua.runtime")


@dataclass(frozen=True, slots=True)
class StepResult:
    session_id: str
    session_changed: bool
    observations_processed: int
    action_submitted: bool
    decision_id: str | None


class Runtime:
    def __init__(
        self,
        config: Config,
        store: Store,
        bridge: BridgeClient | Any,
        policy: BootstrapPolicy | None = None,
    ):
        self.config = config
        self.store = store
        self.bridge = bridge
        self.policy = policy or BootstrapPolicy()
        self.store.ensure_agent(config.agent_id)

    @staticmethod
    def _decision_id(agent_id: str, session_id: str, sequence: int, action_payload: dict[str, Any]) -> str:
        encoded = json.dumps(
            [agent_id, session_id, sequence, action_payload],
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        return "mind-" + hashlib.sha256(encoded).hexdigest()[:32]

    def step(self) -> StepResult:
        session = self.bridge.session()
        session_id = session["session_id"]
        changed = self.store.apply_session(self.config.agent_id, session_id)
        state = self.store.state(self.config.agent_id)
        cursor = int(state["last_observation_sequence"])

        observations = self.bridge.observations(cursor)
        latest: PerceptionFrame | None = None
        novel_count = 0
        processed = 0

        for observation in observations:
            frame = build_frame(observation)
            if frame.sequence <= cursor:
                raise ProtocolError("Bridge vrátil duplicitní nebo klesající observation sequence")
            seen = self.store.seen_appearance_ids(self.config.agent_id, frame.appearance_ids)
            current_novel = len(set(frame.appearance_ids) - seen)
            if self.store.record_observation(self.config.agent_id, session_id, frame):
                processed += 1
                latest = frame
                novel_count = current_novel
                cursor = frame.sequence

        if latest is None:
            return StepResult(session_id, changed, processed, False, None)

        intent = self.policy.choose(latest, novel_count)
        action: dict[str, Any] = {
            "schema_version": 1,
            "agent_id": self.config.agent_id,
            "client_action_id": "",
            "type": intent.action_type,
            "parameters": intent.parameters,
        }
        if intent.duration is not None:
            action["duration"] = float(intent.duration)
        if intent.target_ref is not None:
            action["target_ref"] = intent.target_ref

        decision_id = self._decision_id(
            self.config.agent_id,
            session_id,
            latest.sequence,
            {key: value for key, value in action.items() if key != "client_action_id"},
        )
        action["client_action_id"] = decision_id

        self.store.record_decision(
            decision_id,
            self.config.agent_id,
            session_id,
            latest.sequence,
            action,
            intent.rationale,
        )
        response = self.bridge.submit_action(action)
        self.store.mark_decision_submitted(decision_id, response["request_id"], response["status"])
        return StepResult(session_id, changed, processed, True, decision_id)

    def run_forever(self) -> None:
        backoff = self.config.poll_interval
        while True:
            try:
                self.step()
                backoff = self.config.poll_interval
                time.sleep(self.config.poll_interval)
            except BridgeUnavailable as exc:
                LOG.warning("AluaBridge není dostupný: %s", exc)
                time.sleep(backoff)
                backoff = min(5.0, max(self.config.poll_interval, backoff * 2))
            except BridgeHttpError as exc:
                if not exc.retryable:
                    raise
                LOG.warning("Dočasná chyba AluaBridge: %s", exc)
                time.sleep(backoff)
                backoff = min(5.0, max(self.config.poll_interval, backoff * 2))
