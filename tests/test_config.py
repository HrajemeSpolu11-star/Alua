from __future__ import annotations

from pathlib import Path
import unittest

from alua.config import Config
from alua.errors import ConfigError


class ConfigTests(unittest.TestCase):
    def test_loopback_config_is_valid(self) -> None:
        Config(
            agent_id="alua:1",
            bridge_url="http://127.0.0.1:8787",
            agent_token="a" * 48,
            database_path=Path("x.sqlite3"),
        ).validate()

    def test_remote_bridge_is_rejected(self) -> None:
        with self.assertRaises(ConfigError):
            Config(
                agent_id="alua:1",
                bridge_url="http://example.com:8787",
                agent_token="a" * 48,
                database_path=Path("x.sqlite3"),
            ).validate()


if __name__ == "__main__":
    unittest.main()
