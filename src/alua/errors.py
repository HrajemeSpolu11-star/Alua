from __future__ import annotations


class AluaError(Exception):
    """Base error for Alua runtime."""


class ConfigError(AluaError):
    """Invalid local configuration."""


class ProtocolError(AluaError):
    """Bridge payload violated the expected versioned contract."""


class BridgeUnavailable(AluaError):
    """Bridge could not be reached."""


class BridgeHttpError(AluaError):
    def __init__(self, status: int, code: str, message: str):
        super().__init__(f"{status} {code}: {message}")
        self.status = int(status)
        self.code = str(code)
        self.message = str(message)

    @property
    def retryable(self) -> bool:
        return self.status in {408, 425, 429, 500, 502, 503, 504}
