from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
from urllib.error import HTTPError
from urllib.request import urlopen

import pytest

from pypagekit.development import DevelopmentServer, DevelopmentServerConfig


def test_encoded_backslash_path_is_not_served(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    (root / "safe.txt").write_text("safe", encoding="utf-8")

    session = DevelopmentServer().create(DevelopmentServerConfig(root, port=0))
    thread = Thread(target=session.serve_forever, daemon=True)
    thread.start()
    try:
        connection = HTTPConnection(
            session.info.host,
            session.info.port,
            timeout=2,
        )
        connection.request("GET", "/%5c..%5csafe.txt")
        response = connection.getresponse()
        body = response.read()
        connection.close()

        assert response.status == 404
        assert b"safe" not in body
    finally:
        session.shutdown()
        thread.join(timeout=2)
        session.close()


def test_symlinked_directory_inside_root_is_not_served(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "secret.txt").write_text("protected", encoding="utf-8")
    (root / "linked").symlink_to(outside, target_is_directory=True)

    session = DevelopmentServer().create(DevelopmentServerConfig(root, port=0))
    thread = Thread(target=session.serve_forever, daemon=True)
    thread.start()
    try:
        with pytest.raises(HTTPError) as exc_info:
            urlopen(
                f"{session.info.url}/linked/secret.txt",
                timeout=2,
            )

        assert exc_info.value.code == 404
    finally:
        session.shutdown()
        thread.join(timeout=2)
        session.close()
