from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from urllib.parse import urlsplit

from .errors import ConfigError


@dataclass(frozen=True, slots=True)
class Config:
    agent_id: str
    bridge_url: str
    agent_token: str
    database_path: Path
    poll_interval: float = 0.25
    request_timeout: float = 2.0

    @classmethod
    def from_env(cls) -> "Config":
        config = cls(
            agent_id=os.getenv("ALUA_AGENT_ID", "alua:1").strip(),
            bridge_url=os.getenv("ALUABRIDGE_URL", "http://127.0.0.1:8787").strip().rstrip("/"),
            agent_token=os.getenv("ALUA_AGENT_TOKEN", ""),
            database_path=Path(os.getenv("ALUA_DB_PATH", "data/alua.sqlite3")).expanduser(),
            poll_interval=float(os.getenv("ALUA_POLL_INTERVAL", "0.25")),
            request_timeout=float(os.getenv("ALUA_REQUEST_TIMEOUT", "2.0")),
        )
        config.validate()
        return config

    def validate(self) -> None:
        if not self.agent_id or len(self.agent_id) > 128:
            raise ConfigError("ALUA_AGENT_ID musí mít 1..128 znaků")
        if len(self.agent_token) < 32:
            raise ConfigError("ALUA_AGENT_TOKEN musí mít alespoň 32 znaků")
        if not 0.05 <= self.poll_interval <= 10.0:
            raise ConfigError("ALUA_POLL_INTERVAL musí být 0.05..10 s")
        if not 0.1 <= self.request_timeout <= 30.0:
            raise ConfigError("ALUA_REQUEST_TIMEOUT musí být 0.1..30 s")

        parsed = urlsplit(self.bridge_url)
        if parsed.scheme != "http":
            raise ConfigError("AluaBridge V1 musí používat localhost HTTP")
        if parsed.username or parsed.password or parsed.query or parsed.fragment:
            raise ConfigError("ALUABRIDGE_URL nesmí obsahovat credentials, query ani fragment")
        if parsed.hostname not in {"127.0.0.1", "localhost", "::1"}:
            raise ConfigError("AluaBridge V1 smí být dostupný pouze přes loopback")
        if parsed.path not in {"", "/"}:
            raise ConfigError("ALUABRIDGE_URL nesmí obsahovat cestu")
        if parsed.port is not None and not 1 <= parsed.port <= 65535:
            raise ConfigError("Port AluaBridge je mimo rozsah")
