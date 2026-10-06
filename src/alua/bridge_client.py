from __future__ import annotations

import json
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import Config
from .errors import BridgeHttpError, BridgeUnavailable, ProtocolError
from .schema import (
    validate_action_response,
    validate_observation_response,
    validate_session,
)


class BridgeClient:
    def __init__(self, config: Config):
        self.config = config

    def _request_json(self, method: str, path: str, body: dict[str, Any] | None = None, auth: bool = True) -> Any:
        data = None
        headers = {"Accept": "application/json"}
        if body is not None:
            data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
            headers["Content-Type"] = "application/json"
        if auth:
            headers["Authorization"] = "Bearer " + self.config.agent_token
        request = Request(self.config.bridge_url + path, data=data, headers=headers, method=method)
        try:
            with urlopen(request, timeout=self.config.request_timeout) as response:
                raw = response.read(524_289)
                if len(raw) > 524_288:
                    raise ProtocolError("Bridge response překročila bezpečný limit")
        except HTTPError as exc:
            raw = exc.read(131_073)
            code = "http_error"
            message = str(exc.reason)
            try:
                parsed = json.loads(raw.decode("utf-8"))
                error = parsed.get("error", {})
                code = str(error.get("code", code))
                message = str(error.get("message", message))
            except Exception:
                pass
            raise BridgeHttpError(exc.code, code, message) from exc
        except (URLError, TimeoutError, OSError) as exc:
            raise BridgeUnavailable(str(exc)) from exc

        try:
            return json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ProtocolError("Bridge vrátil neplatný JSON") from exc

    def health(self) -> dict[str, Any]:
        value = self._request_json("GET", "/health", auth=False)
        if not isinstance(value, dict) or value.get("service") != "aluabridge":
            raise ProtocolError("Neplatná /health odpověď")
        return value

    def session(self) -> dict[str, Any]:
        query = urlencode({"agent_id": self.config.agent_id})
        value = self._request_json("GET", "/v1/agent/session?" + query)
        return validate_session(value, self.config.agent_id)

    def observations(self, after_sequence: int) -> list[dict[str, Any]]:
        query = urlencode({"agent_id": self.config.agent_id, "after_sequence": int(after_sequence)})
        value = self._request_json("GET", "/v1/agent/observations?" + query)
        return validate_observation_response(value, self.config.agent_id)

    def submit_action(self, action: dict[str, Any]) -> dict[str, Any]:
        value = self._request_json("POST", "/v1/agent/actions", action)
        return validate_action_response(value)
