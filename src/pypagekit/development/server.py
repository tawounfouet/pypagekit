"""Safe local static HTTP server for generated PyPageKit output."""

from __future__ import annotations

import os
import re
from contextlib import suppress
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path, PurePosixPath
from threading import Lock
from typing import ClassVar
from urllib.parse import unquote, urlsplit

from .exceptions import DevelopmentServerBindError
from .model import DevelopmentServerConfig, DevelopmentServerInfo

_FORBIDDEN_SENTINEL = ".pypagekit-forbidden-resource"
_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_LIVE_RELOAD_SCRIPT_PATH = "/.pypagekit/live-reload.js"
_LIVE_RELOAD_REVISION_PATH = "/.pypagekit/live-reload/revision"
_LIVE_RELOAD_MARKER = b"data-pypagekit-live-reload"
_LIVE_RELOAD_TAG = (
    b'<script src="/.pypagekit/live-reload.js" '
    b"data-pypagekit-live-reload></script>"
)
_LIVE_RELOAD_SCRIPT = b"""(() => {
  let revision = null;

  async function poll() {
    try {
      const response = await fetch(
        "/.pypagekit/live-reload/revision",
        { cache: "no-store" }
      );
      if (!response.ok) return;
      const next = Number(await response.text());
      if (revision === null) {
        revision = next;
        return;
      }
      if (next !== revision) {
        window.location.reload();
      }
    } catch {
      // The development server may be restarting or shutting down.
    }
  }

  poll();
  window.setInterval(poll, 500);
})();
"""


class _LiveReloadState:
    def __init__(self) -> None:
        self._lock = Lock()
        self._revision = 0

    @property
    def revision(self) -> int:
        with self._lock:
            return self._revision

    def notify(self) -> int:
        with self._lock:
            self._revision += 1
            return self._revision


class _DevelopmentHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True
    live_reload_state: _LiveReloadState | None = None


class _StaticRequestHandler(SimpleHTTPRequestHandler):
    """Serve a static root without listings or symlink escapes."""

    server_version = "PyPageKitDevelopmentServer"
    _root: ClassVar[Path]
    _resolved_root: ClassVar[Path]
    _live_reload_state: ClassVar[_LiveReloadState | None]

    def do_GET(self) -> None:
        """Serve static content and optional live-reload resources."""

        if self._serve_live_reload_resource(head_only=False):
            return
        if self._serve_live_reload_html(head_only=False):
            return
        super().do_GET()

    def do_HEAD(self) -> None:
        """Serve static headers and optional live-reload resource headers."""

        if self._serve_live_reload_resource(head_only=True):
            return
        if self._serve_live_reload_html(head_only=True):
            return
        super().do_HEAD()

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
            "\" in decoded_path
            or "\x00" in decoded_path
            or any(ord(character) < 32 or ord(character) == 0x7F for character in decoded_path)
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
            "default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        )
        self.send_header("Referrer-Policy", "no-referrer")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("X-Frame-Options", "DENY")
        super().end_headers()

    def log_message(self, format: str, *args: object) -> None:
        """Keep request logging out of the framework's console layer."""

        del format, args

    def _serve_live_reload_resource(self, *, head_only: bool) -> bool:
        state = self._live_reload_state
        if state is None:
            return False

        request_path = urlsplit(self.path).path
        if request_path == _LIVE_RELOAD_SCRIPT_PATH:
            self._send_bytes(
                _LIVE_RELOAD_SCRIPT,
                content_type="text/javascript; charset=utf-8",
                head_only=head_only,
            )
            return True
        if request_path == _LIVE_RELOAD_REVISION_PATH:
            self._send_bytes(
                str(state.revision).encode("ascii"),
                content_type="text/plain; charset=ascii",
                head_only=head_only,
            )
            return True
        return False

    def _serve_live_reload_html(self, *, head_only: bool) -> bool:
        if self._live_reload_state is None:
            return False

        target = self._html_target()
        if target is None:
            return False

        try:
            content = target.read_bytes()
            target_stat = target.stat(follow_symlinks=False)
        except OSError:
            return False

        if _LIVE_RELOAD_MARKER not in content:
            content = _inject_live_reload_tag(content)

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Last-Modified", self.date_time_string(target_stat.st_mtime))
        self.end_headers()
        if not head_only:
            self.wfile.write(content)
        return True

    def _html_target(self) -> Path | None:
        translated = Path(self.translate_path(self.path))
        if translated.is_dir():
            if not urlsplit(self.path).path.endswith("/"):
                return None
            translated = translated / "index.html"

        if translated.suffix.lower() != ".html":
            return None
        if translated.is_symlink() or not translated.is_file():
            return None

        try:
            translated.relative_to(self._resolved_root)
        except ValueError:
            return None
        return translated

    def _send_bytes(
        self,
        content: bytes,
        *,
        content_type: str,
        head_only: bool,
    ) -> None:
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        if not head_only:
            self.wfile.write(content)

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
        self._live_reload_state = server.live_reload_state

    @property
    def info(self) -> DevelopmentServerInfo:
        return self._info

    @property
    def live_reload(self) -> bool:
        """Return whether this server session exposes live reload resources."""

        return self._live_reload_state is not None

    def notify_reload(self) -> int:
        """Advance the live reload revision after a successful rebuild."""

        if self._live_reload_state is None:
            raise RuntimeError("Live reload is not enabled for this development server session.")
        return self._live_reload_state.notify()

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
        *,
        live_reload: bool = False,
    ) -> DevelopmentServerSession:
        """Bind a server and return an explicitly managed session."""

        if not isinstance(config, DevelopmentServerConfig):
            raise TypeError("Development server config must be a DevelopmentServerConfig object.")
        if not isinstance(live_reload, bool):
            raise TypeError("Development server live_reload flag must be a bool.")

        live_reload_state = _LiveReloadState() if live_reload else None
        handler = _handler_for(
            config.root,
            live_reload_state=live_reload_state,
        )

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
        server.live_reload_state = live_reload_state
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


def _handler_for(
    root: Path,
    *,
    live_reload_state: _LiveReloadState | None,
) -> type[_StaticRequestHandler]:
    root_path = root
    resolved_root = root.resolve(strict=True)
    reload_state = live_reload_state

    class BoundStaticRequestHandler(_StaticRequestHandler):
        _root = root_path
        _resolved_root = resolved_root
        _live_reload_state = reload_state

    return BoundStaticRequestHandler


def _inject_live_reload_tag(content: bytes) -> bytes:
    lower = content.lower()
    marker = b"</body>"
    index = lower.rfind(marker)
    if index < 0:
        return content + _LIVE_RELOAD_TAG
    return content[:index] + _LIVE_RELOAD_TAG + content[index:]


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
