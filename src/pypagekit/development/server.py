"""Safe local static HTTP server for generated PyPageKit output."""

from __future__ import annotations

import os
import re
from contextlib import suppress
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from typing import ClassVar
from urllib.parse import unquote, urlsplit

from .exceptions import DevelopmentServerBindError
from .model import DevelopmentServerConfig, DevelopmentServerInfo

_FORBIDDEN_SENTINEL = ".pypagekit-forbidden-resource"
_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")


class _DevelopmentHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True


class _StaticRequestHandler(SimpleHTTPRequestHandler):
    """Serve a static root without listings or symlink escapes."""

    server_version = "PyPageKitDevelopmentServer"
    _root: ClassVar[Path]
    _resolved_root: ClassVar[Path]

    def translate_path(self, path: str) -> str:
        """Translate one URL path while keeping it inside the static root."""

        raw_path = urlsplit(path).path
        if _PERCENT_ESCAPE_RE.search(raw_path):
            return str(self._forbidden_path())

        try:
            decoded_path = unquote(raw_path, errors="strict")
        except UnicodeDecodeError:
            return str(self._forbidden_path())

        if (
            "\\" in decoded_path
            or "\x00" in decoded_path
            or any(
                ord(character) < 32 or ord(character) == 0x7F
                for character in decoded_path
            )
        ):
            return str(self._forbidden_path())

        logical_path = PurePosixPath(decoded_path)
        if any(part in {".", ".."} for part in logical_path.parts):
            return str(self._forbidden_path())

        parts = tuple(part for part in logical_path.parts if part not in {"/", ""})
        candidate = self._root.joinpath(*parts)

        if _path_contains_symlink(self._root, candidate):
            return str(self._forbidden_path())

        resolved_candidate = candidate.resolve(strict=False)
        try:
            resolved_candidate.relative_to(self._resolved_root)
        except ValueError:
            return str(self._forbidden_path())

        return str(resolved_candidate)

    def list_directory(self, path: str | os.PathLike[str]) -> None:
        """Disable automatic directory listings."""

        del path
        self.send_error(HTTPStatus.NOT_FOUND, "Directory listing is disabled")

    def end_headers(self) -> None:
        """Emit defensive headers for local development responses."""

        self.send_header("Cache-Control", "no-store")
        self.send_header(
            "Content-Security-Policy",
            "default-src 'self'; object-src 'none'; base-uri 'none'; "
            "frame-ancestors 'none'",
        )
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Keep request logging out of the framework's console layer."""

        del format, args

    def _forbidden_path(self) -> Path:
        return self._resolved_root / _FORBIDDEN_SENTINEL


class DevelopmentServerSession:
    """Bound HTTP server session with explicit lifecycle control."""

    def __init__(
        self,
        server: _DevelopmentHTTPServer,
        info: DevelopmentServerInfo,
    ) -> None:
        self._server = server
        self._info = info

    @property
    def info(self) -> DevelopmentServerInfo:
        return self._info

    def serve_forever(self) -> None:
        """Block while serving requests until shutdown is requested."""

        self._server.serve_forever()

    def shutdown(self) -> None:
        """Stop a running serve_forever loop."""

        self._server.shutdown()

    def close(self) -> None:
        """Close the bound server socket."""

        self._server.server_close()

    def __enter__(self) -> DevelopmentServerSession:
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        del exc_type, exc_value, traceback
        self.close()


class DevelopmentServer:
    """Create and run local static servers without changing process cwd."""

    def create(
        self,
        config: DevelopmentServerConfig,
    ) -> DevelopmentServerSession:
        """Bind a server and return an explicitly managed session."""

        if not isinstance(config, DevelopmentServerConfig):
            raise TypeError("Development server config must be a DevelopmentServerConfig object.")

        handler = _handler_for(config.root)

        try:
            server = _DevelopmentHTTPServer((config.host, config.port), handler)
        except OSError as exc:
            raise DevelopmentServerBindError(
                f"Unable to bind development server to {config.host}:{config.port}."
            ) from exc

        bound_host = str(server.server_address[0])
        bound_port = int(server.server_address[1])
        info = DevelopmentServerInfo(
            root=config.root,
            host=bound_host,
            port=bound_port,
        )
        return DevelopmentServerSession(server, info)

    def serve(
        self,
        config: DevelopmentServerConfig,
    ) -> DevelopmentServerInfo:
        """Serve until interrupted and return the bound server information."""

        with self.create(config) as session:
            info = session.info
            with suppress(KeyboardInterrupt):
                session.serve_forever()
            return info


def _handler_for(root: Path) -> type[_StaticRequestHandler]:
    root_path = root
    resolved_root = root.resolve(strict=True)

    class BoundStaticRequestHandler(_StaticRequestHandler):
        _root = root_path
        _resolved_root = resolved_root

    return BoundStaticRequestHandler


def _path_contains_symlink(root: Path, candidate: Path) -> bool:
    try:
        relative = candidate.relative_to(root)
    except ValueError:
        return True

    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            return True
    return False


__all__ = [
    "DevelopmentServer",
    "DevelopmentServerSession",
]
