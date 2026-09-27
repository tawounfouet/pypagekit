from dataclasses import FrozenInstanceError
from pathlib import Path

import pytest

from pypagekit.development import (
    DevelopmentServerConfig,
    DevelopmentServerInfo,
    InvalidDevelopmentHostError,
    InvalidDevelopmentPortError,
    InvalidDevelopmentRootError,
)


def test_development_server_config_defaults(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()

    config = DevelopmentServerConfig(root)

    assert config.root == root
    assert config.host == "127.0.0.1"
    assert config.port == 8000


def test_development_server_info_exposes_url(tmp_path: Path) -> None:
    info = DevelopmentServerInfo(tmp_path, "127.0.0.1", 8123)

    assert info.url == "http://127.0.0.1:8123"


def test_wildcard_bind_uses_localhost_for_display(tmp_path: Path) -> None:
    info = DevelopmentServerInfo(tmp_path, "0.0.0.0", 8123)

    assert info.url == "http://localhost:8123"


@pytest.mark.parametrize(
    "host",
    [
        "",
        " localhost",
        "local host",
        "http://localhost",
        "host/name",
        "host?query",
        "::1",
    ],
)
def test_invalid_hosts_fail(tmp_path: Path, host: str) -> None:
    root = tmp_path / "dist"
    root.mkdir()

    with pytest.raises(InvalidDevelopmentHostError):
        DevelopmentServerConfig(root, host=host)


@pytest.mark.parametrize("port", [-1, 65536])
def test_invalid_ports_fail(tmp_path: Path, port: int) -> None:
    root = tmp_path / "dist"
    root.mkdir()

    with pytest.raises(InvalidDevelopmentPortError):
        DevelopmentServerConfig(root, port=port)


def test_ephemeral_port_zero_is_valid_for_python_api(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()

    assert DevelopmentServerConfig(root, port=0).port == 0


def test_boolean_port_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()

    with pytest.raises(TypeError, match="integer"):
        DevelopmentServerConfig(root, port=True)


def test_missing_root_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(InvalidDevelopmentRootError, match="does not exist"):
        DevelopmentServerConfig(tmp_path / "missing")


def test_file_root_is_rejected(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.write_text("file", encoding="utf-8")

    with pytest.raises(InvalidDevelopmentRootError, match="directory"):
        DevelopmentServerConfig(root)


def test_symlink_root_is_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    root = tmp_path / "dist"
    root.symlink_to(real, target_is_directory=True)

    with pytest.raises(InvalidDevelopmentRootError, match="symlink"):
        DevelopmentServerConfig(root)


def test_symlinked_root_ancestor_is_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real"
    root = real / "dist"
    root.mkdir(parents=True)
    link = tmp_path / "linked"
    link.symlink_to(real, target_is_directory=True)

    with pytest.raises(InvalidDevelopmentRootError, match="ancestor"):
        DevelopmentServerConfig(link / "dist")


def test_config_is_immutable(tmp_path: Path) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    config = DevelopmentServerConfig(root)

    with pytest.raises(FrozenInstanceError):
        config.port = 9000  # type: ignore[misc]
