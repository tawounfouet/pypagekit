from collections.abc import Iterator
from contextlib import contextmanager
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from pypagekit.development import (
    DevelopmentServer,
    DevelopmentServerBindError,
    DevelopmentServerConfig,
    DevelopmentServerSession,
)


@contextmanager
def running_server(
    root: Path,
    *,
    live_reload: bool = False,
) -> Iterator[DevelopmentServerSession]:
    session = DevelopmentServer().create(
        DevelopmentServerConfig(root, port=0),
        live_reload=live_reload,
    )
    thread = Thread(target=session.serve_forever, daemon=True)
    thread.start()
    try:
        yield session
    finally:
        session.shutdown()
        thread.join(timeout=2)
        session.close()


def test_server_serves_root_index_and_disables_cache(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    (root / "index.html").write_text("<h1>Home</h1>", encoding="utf-8")

    with (
        running_server(root) as session,
        urlopen(f"{session.info.url}/", timeout=2) as response,
    ):
        body = response.read().decode("utf-8")
        assert response.status == 200
        assert response.headers["Cache-Control"] == "no-store"

    assert body == "<h1>Home</h1>"


def test_server_serves_pretty_url_index(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    page = root / "about" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text("<h1>About</h1>", encoding="utf-8")

    with (
        running_server(root) as session,
        urlopen(f"{session.info.url}/about/", timeout=2) as response,
    ):
        body = response.read().decode("utf-8")

    assert body == "<h1>About</h1>"


def test_server_serves_binary_assets(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    asset = root / "assets" / "logo.bin"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"\x00\x01asset")

    with (
        running_server(root) as session,
        urlopen(
            f"{session.info.url}/assets/logo.bin",
            timeout=2,
        ) as response,
    ):
        body = response.read()

    assert body == b"\x00\x01asset"


def test_directory_listing_is_disabled(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    (root / "private").mkdir(parents=True)
    (root / "private" / "secret.txt").write_text("secret", encoding="utf-8")

    with running_server(root) as session, pytest.raises(HTTPError) as exc_info:
        urlopen(f"{session.info.url}/private/", timeout=2)

    assert exc_info.value.code == 404


def test_missing_resource_returns_404(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()

    with running_server(root) as session, pytest.raises(HTTPError) as exc_info:
        urlopen(f"{session.info.url}/missing.txt", timeout=2)

    assert exc_info.value.code == 404


def test_encoded_traversal_cannot_escape_root(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    (tmp_path / "secret.txt").write_text("outside", encoding="utf-8")

    with running_server(root) as session:
        connection = HTTPConnection(
            session.info.host,
            session.info.port,
            timeout=2,
        )
        connection.request("GET", "/%2e%2e/secret.txt")
        response = connection.getresponse()
        body = response.read()
        connection.close()

    assert response.status == 404
    assert b"outside" not in body


def test_symlinked_file_inside_root_is_not_served(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("protected", encoding="utf-8")
    (root / "leak.txt").symlink_to(outside)

    with running_server(root) as session, pytest.raises(HTTPError) as exc_info:
        urlopen(f"{session.info.url}/leak.txt", timeout=2)

    assert exc_info.value.code == 404


def test_server_creation_does_not_change_process_cwd(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    before = Path.cwd()

    session = DevelopmentServer().create(DevelopmentServerConfig(root, port=0))
    session.close()

    assert Path.cwd() == before


def test_bound_info_reports_ephemeral_port(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()

    session = DevelopmentServer().create(DevelopmentServerConfig(root, port=0))
    try:
        assert session.info.port > 0
        assert session.info.host
    finally:
        session.close()


def test_bind_conflict_raises_framework_error(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    first = DevelopmentServer().create(DevelopmentServerConfig(root, port=0))

    try:
        with pytest.raises(DevelopmentServerBindError):
            DevelopmentServer().create(
                DevelopmentServerConfig(
                    root,
                    host=first.info.host,
                    port=first.info.port,
                )
            )
    finally:
        first.close()



def test_default_server_does_not_inject_live_reload(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    original = b"<html><body><h1>Home</h1></body></html>"
    (root / "index.html").write_bytes(original)

    with (
        running_server(root) as session,
        urlopen(f"{session.info.url}/", timeout=2) as response,
    ):
        body = response.read()

    assert body == original
    assert b"data-pypagekit-live-reload" not in body
    assert session.live_reload is False

    with pytest.raises(RuntimeError, match="not enabled"):
        session.notify_reload()


def test_live_reload_server_injects_external_script_without_mutating_file(
    tmp_path: Path,
) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    original = b"<html><body><h1>Home</h1></body></html>"
    target = root / "index.html"
    target.write_bytes(original)

    with (
        running_server(root, live_reload=True) as session,
        urlopen(f"{session.info.url}/", timeout=2) as response,
    ):
        body = response.read()
        csp = response.headers["Content-Security-Policy"]

    assert session.live_reload is True
    assert b'data-pypagekit-live-reload' in body
    assert b'src="/.pypagekit/live-reload.js"' in body
    assert body.index(b"data-pypagekit-live-reload") < body.index(b"</body>")
    assert target.read_bytes() == original
    assert "'unsafe-inline'" not in csp


def test_live_reload_revision_endpoint_advances_after_notification(
    tmp_path: Path,
) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    (root / "index.html").write_text("<p>Home</p>", encoding="utf-8")

    with running_server(root, live_reload=True) as session:
        with urlopen(
            f"{session.info.url}/.pypagekit/live-reload/revision",
            timeout=2,
        ) as response:
            assert response.read() == b"0"
            assert response.headers["Cache-Control"] == "no-store"

        assert session.notify_reload() == 1
        assert session.notify_reload() == 2

        with urlopen(
            f"{session.info.url}/.pypagekit/live-reload/revision",
            timeout=2,
        ) as response:
            assert response.read() == b"2"


def test_live_reload_script_polls_revision_endpoint(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    (root / "index.html").write_text("<p>Home</p>", encoding="utf-8")

    with (
        running_server(root, live_reload=True) as session,
        urlopen(
            f"{session.info.url}/.pypagekit/live-reload.js",
            timeout=2,
        ) as response,
    ):
        script = response.read().decode("utf-8")

    assert "/.pypagekit/live-reload/revision" in script
    assert "window.location.reload()" in script
    assert "window.setInterval(poll, 500)" in script


def test_live_reload_resource_is_not_reserved_when_mode_is_disabled(
    tmp_path: Path,
) -> None:
    root = tmp_path / "dist"
    resource = root / ".pypagekit" / "live-reload.js"
    resource.parent.mkdir(parents=True)
    resource.write_text("user-resource", encoding="utf-8")

    with (
        running_server(root) as session,
        urlopen(
            f"{session.info.url}/.pypagekit/live-reload.js",
            timeout=2,
        ) as response,
    ):
        body = response.read().decode("utf-8")

    assert body == "user-resource"


def test_live_reload_mode_does_not_modify_binary_responses(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    asset = root / "asset.bin"
    asset.parent.mkdir(parents=True, exist_ok=True)
    payload = b"\x00\x01binary\xff"
    asset.write_bytes(payload)

    with (
        running_server(root, live_reload=True) as session,
        urlopen(f"{session.info.url}/asset.bin", timeout=2) as response,
    ):
        body = response.read()

    assert body == payload


def test_live_reload_html_head_reports_injected_content_length(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    (root / "index.html").write_text(
        "<html><body>Home</body></html>",
        encoding="utf-8",
    )

    with running_server(root, live_reload=True) as session:
        connection = HTTPConnection(
            session.info.host,
            session.info.port,
            timeout=2,
        )
        connection.request("HEAD", "/index.html")
        response = connection.getresponse()
        body = response.read()
        content_length = int(response.headers["Content-Length"])
        connection.close()

        with urlopen(f"{session.info.url}/index.html", timeout=2) as get_response:
            get_body = get_response.read()

    assert body == b""
    assert content_length == len(get_body)
