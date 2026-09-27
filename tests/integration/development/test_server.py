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
def running_server(root: Path) -> Iterator[DevelopmentServerSession]:
    session = DevelopmentServer().create(
        DevelopmentServerConfig(root, port=0)
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

    with running_server(root) as session:
        with urlopen(f"{session.info.url}/", timeout=2) as response:
            body = response.read().decode("utf-8")
            assert response.status == 200
            assert response.headers["Cache-Control"] == "no-store"

    assert body == "<h1>Home</h1>"


def test_server_serves_pretty_url_index(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    page = root / "about" / "index.html"
    page.parent.mkdir(parents=True)
    page.write_text("<h1>About</h1>", encoding="utf-8")

    with running_server(root) as session:
        with urlopen(f"{session.info.url}/about/", timeout=2) as response:
            body = response.read().decode("utf-8")

    assert body == "<h1>About</h1>"


def test_server_serves_binary_assets(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    asset = root / "assets" / "logo.bin"
    asset.parent.mkdir(parents=True)
    asset.write_bytes(b"\x00\x01asset")

    with running_server(root) as session:
        with urlopen(
            f"{session.info.url}/assets/logo.bin",
            timeout=2,
        ) as response:
            body = response.read()

    assert body == b"\x00\x01asset"


def test_directory_listing_is_disabled(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    (root / "private").mkdir(parents=True)
    (root / "private" / "secret.txt").write_text("secret", encoding="utf-8")

    with running_server(root) as session:
        with pytest.raises(HTTPError) as exc_info:
            urlopen(f"{session.info.url}/private/", timeout=2)

    assert exc_info.value.code == 404


def test_missing_resource_returns_404(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()

    with running_server(root) as session:
        with pytest.raises(HTTPError) as exc_info:
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

    with running_server(root) as session:
        with pytest.raises(HTTPError) as exc_info:
            urlopen(f"{session.info.url}/leak.txt", timeout=2)

    assert exc_info.value.code == 404


def test_server_creation_does_not_change_process_cwd(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    before = Path.cwd()

    session = DevelopmentServer().create(
        DevelopmentServerConfig(root, port=0)
    )
    session.close()

    assert Path.cwd() == before


def test_bound_info_reports_ephemeral_port(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()

    session = DevelopmentServer().create(
        DevelopmentServerConfig(root, port=0)
    )
    try:
        assert session.info.port > 0
        assert session.info.host
    finally:
        session.close()


def test_bind_conflict_raises_framework_error(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    first = DevelopmentServer().create(
        DevelopmentServerConfig(root, port=0)
    )

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
