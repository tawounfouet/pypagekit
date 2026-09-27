"""Immutable development server configuration and runtime information."""

from dataclasses import dataclass
from pathlib import Path

from .exceptions import (
    InvalidDevelopmentHostError,
    InvalidDevelopmentPortError,
    InvalidDevelopmentRootError,
)


@dataclass(frozen=True, slots=True)
class DevelopmentServerConfig:
    """Validated static development server configuration."""

    root: Path
    host: str = "127.0.0.1"
    port: int = 8000

    def __post_init__(self) -> None:
        _validate_root(self.root)
        _validate_host(self.host)
        _validate_port(self.port)


@dataclass(frozen=True, slots=True)
class DevelopmentServerInfo:
    """Actual address and root used by a bound development server."""

    root: Path
    host: str
    port: int

    @property
    def url(self) -> str:
        """Return the HTTP URL for the bound server."""

        display_host = "localhost" if self.host == "0.0.0.0" else self.host
        return f"http://{display_host}:{self.port}"


def _validate_root(root: Path) -> None:
    if not isinstance(root, Path):
        raise TypeError("Development server root must be a pathlib.Path.")
    if not root.exists():
        raise InvalidDevelopmentRootError(f"Development server root '{root}' does not exist.")
    if root.is_symlink():
        raise InvalidDevelopmentRootError(
            f"Development server root '{root}' must not be a symlink."
        )
    if not root.is_dir():
        raise InvalidDevelopmentRootError(f"Development server root '{root}' must be a directory.")

    cursor = root.parent
    while True:
        if cursor.is_symlink():
            raise InvalidDevelopmentRootError(
                f"Development server root ancestor '{cursor}' must not be a symlink."
            )
        if cursor == cursor.parent:
            break
        cursor = cursor.parent


def _validate_host(host: str) -> None:
    if not isinstance(host, str):
        raise TypeError("Development server host must be a string.")

    if (
        not host
        or host != host.strip()
        or len(host) > 253
        or any(character.isspace() or ord(character) < 32 for character in host)
        or any(character in host for character in "/\\?#")
        or "://" in host
        or ":" in host
    ):
        raise InvalidDevelopmentHostError(
            "Development server host must be a hostname or IPv4 address."
        )


def _validate_port(port: int) -> None:
    if not isinstance(port, int) or isinstance(port, bool):
        raise TypeError("Development server port must be an integer.")
    if port < 0 or port > 65535:
        raise InvalidDevelopmentPortError("Development server port must be between 0 and 65535.")


__all__ = [
    "DevelopmentServerConfig",
    "DevelopmentServerInfo",
]
