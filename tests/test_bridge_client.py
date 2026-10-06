from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import threading
import unittest

from alua.bridge_client import BridgeClient
from alua.config import Config


class Handler(BaseHTTPRequestHandler):
    authorization = None

    def log_message(self, fmt, *args):
        pass

    def do_GET(self):
        Handler.authorization = self.headers.get("Authorization")
        if self.path == "/health":
            body = {"status": "ok", "service": "aluabridge", "schema_version": 1}
        elif self.path.startswith("/v1/agent/session?"):
            body = {
                "schema_version": 1,
                "agent_id": "alua:1",
                "session_id": "s1",
                "last_observation_sequence": 0,
                "last_action_sequence": 0,
            }
        else:
            body = {"schema_version": 1, "agent_id": "alua:1", "observations": []}
        raw = json.dumps(body).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)


class BridgeClientTests(unittest.TestCase):
    def setUp(self):
        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.config = Config(
            agent_id="alua:1",
            bridge_url=f"http://127.0.0.1:{self.server.server_address[1]}",
            agent_token="a" * 48,
            database_path=Path("unused.sqlite3"),
        )

    def tearDown(self):
        self.server.shutdown()
        self.thread.join(timeout=2)
        self.server.server_close()

    def test_session_uses_agent_bearer(self):
        client = BridgeClient(self.config)
        session = client.session()
        self.assertEqual(session["session_id"], "s1")
        self.assertEqual(Handler.authorization, "Bearer " + ("a" * 48))

    def test_health_does_not_send_agent_token(self):
        client = BridgeClient(self.config)
        client.health()
        self.assertIsNone(Handler.authorization)


if __name__ == "__main__":
    unittest.main()
