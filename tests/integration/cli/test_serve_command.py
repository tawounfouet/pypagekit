import re
from pathlib import Path, PurePosixPath
from typing import ClassVar

import pytest
from typer.testing import CliRunner

from pypagekit import Page, Route
from pypagekit.build import BuildPlan, PageBuildEntry
from pypagekit.cli.app import app
from pypagekit.cli.commands.serve import _ProjectPlanLoadError
from pypagekit.cli.exit_codes import EXECUTION_ERROR, SUCCESS, USAGE_ERROR
from pypagekit.development import (
    DevelopmentServerConfig,
    DevelopmentServerInfo,
    WatchChangeBatch,
    WatchSnapshot,
)

runner = CliRunner()
_ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(output: str) -> str:
    return _ANSI_RE.sub("", output)


def test_serve_help_succeeds() -> None:
    result = runner.invoke(app, ["serve", "--help"])

    assert result.exit_code == SUCCESS
    output = _plain(result.output)
    assert "Serve generated static output for local development." in output
    assert "--host" in output
    assert "--port" in output
    assert "--watch" in output
    assert "--entry" in output
    assert "--poll-interval" in output
    assert "--debounce-interval" in output


def test_serve_missing_default_root_is_execution_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["serve"])

    assert result.exit_code == EXECUTION_ERROR
    assert "Development server failed:" in result.stderr
    assert "does not exist" in result.stderr


@pytest.mark.parametrize("port", ["0", "65536"])
def test_serve_invalid_cli_port_is_usage_error(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    port: str,
) -> None:
    root = tmp_path / "dist"
    root.mkdir()
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["serve", "--port", port])

    assert result.exit_code == USAGE_ERROR


class _FakeSession:
    def __init__(self, root: Path) -> None:
        self.info = DevelopmentServerInfo(root, "127.0.0.1", 9123)
        self.served = False
        self.closed = False
        self.shutdown_called = False
        self.reload_revisions: list[int] = []

    def __enter__(self) -> "_FakeSession":
        return self

    def __exit__(
        self,
        exc_type: object,
        exc_value: object,
        traceback: object,
    ) -> None:
        del exc_type, exc_value, traceback
        self.closed = True

    def serve_forever(self) -> None:
        self.served = True

    def shutdown(self) -> None:
        self.shutdown_called = True

    def notify_reload(self) -> int:
        revision = len(self.reload_revisions) + 1
        self.reload_revisions.append(revision)
        return revision


def test_serve_delegates_to_development_service(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = tmp_path / "public"
    root.mkdir()
    captured: list[DevelopmentServerConfig] = []
    session = _FakeSession(root)

    def fake_create(
        self: object,
        config: DevelopmentServerConfig,
    ) -> _FakeSession:
        del self
        captured.append(config)
        return session

    monkeypatch.setattr(
        "pypagekit.cli.commands.serve.DevelopmentServer.create",
        fake_create,
    )

    result = runner.invoke(
        app,
        [
            "serve",
            str(root),
            "--host",
            "127.0.0.1",
            "--port",
            "9000",
        ],
    )

    assert result.exit_code == SUCCESS
    config = captured[0]
    assert config.root == root
    assert config.host == "127.0.0.1"
    assert config.port == 9000
    assert session.served
    assert session.closed
    assert "http://127.0.0.1:9123" in result.stdout


def _page_plan(content: str) -> BuildPlan:
    route = Route("/", Page("Home"))
    return BuildPlan(
        pages=[
            PageBuildEntry(
                route,
                PurePosixPath("index.html"),
                content,
            )
        ]
    )


class _FakeWatcher:
    instances: ClassVar[list["_FakeWatcher"]] = []

    def __init__(
        self,
        root: Path,
        *,
        ignored_paths: tuple[PurePosixPath, ...],
    ) -> None:
        self.root = root
        self.ignored_paths = ignored_paths
        self.wait_count = 0
        self.initial = WatchSnapshot(root)
        self.changed = WatchSnapshot(root)
        type(self).instances.append(self)

    def snapshot(self) -> WatchSnapshot:
        return self.initial

    def wait_for_changes(
        self,
        previous: WatchSnapshot,
        *,
        poll_interval: float,
        debounce_interval: float,
        timeout: float | None,
    ) -> WatchChangeBatch | None:
        del previous, poll_interval, debounce_interval, timeout
        self.wait_count += 1
        if self.wait_count == 1:
            return WatchChangeBatch(self.initial, self.changed, ())
        raise KeyboardInterrupt


def test_serve_watch_builds_incrementally_and_notifies_live_reload(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "site.py").write_text("# test entry\n", encoding="utf-8")
    _FakeWatcher.instances.clear()

    plans = iter(
        [
            _page_plan("<html><body>before</body></html>"),
            _page_plan("<html><body>after</body></html>"),
        ]
    )
    monkeypatch.setattr(
        "pypagekit.cli.commands.serve._load_project_plan",
        lambda project_root, entry_path: next(plans),
    )
    monkeypatch.setattr(
        "pypagekit.cli.commands.serve.DevelopmentWatcher",
        _FakeWatcher,
    )

    session = _FakeSession(tmp_path / "dist")
    create_calls: list[tuple[DevelopmentServerConfig, bool]] = []

    def fake_create(
        self: object,
        config: DevelopmentServerConfig,
        *,
        live_reload: bool = False,
    ) -> _FakeSession:
        del self
        create_calls.append((config, live_reload))
        return session

    monkeypatch.setattr(
        "pypagekit.cli.commands.serve.DevelopmentServer.create",
        fake_create,
    )

    result = runner.invoke(app, ["serve", "--watch"])

    assert result.exit_code == SUCCESS
    assert (tmp_path / "dist" / "index.html").read_text(encoding="utf-8") == (
        "<html><body>after</body></html>"
    )
    assert create_calls[0][1] is True
    assert create_calls[0][0].root == tmp_path / "dist"
    assert session.reload_revisions == [1]
    assert session.shutdown_called is True
    assert _FakeWatcher.instances[0].ignored_paths[-1] == PurePosixPath("dist")
    assert "with watch + live reload" in result.stdout
    assert "Rebuilt 1 file(s), removed 0 file(s)" in result.stdout


def test_serve_watch_requires_project_entry(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    result = runner.invoke(app, ["serve", "--watch"])

    assert result.exit_code == EXECUTION_ERROR
    stderr = " ".join(_plain(result.stderr).split())
    assert "Development watch failed:" in stderr
    assert "does not exist" in stderr


def test_serve_watch_rejects_entry_outside_project_root(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    project = tmp_path / "project"
    project.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("site = None\n", encoding="utf-8")
    monkeypatch.chdir(project)

    result = runner.invoke(
        app,
        [
            "serve",
            "--watch",
            "--entry",
            str(outside),
        ],
    )

    assert result.exit_code == EXECUTION_ERROR
    stderr = " ".join(_plain(result.stderr).split())
    assert "must remain inside the current project root" in stderr


def test_serve_watch_rebuild_failure_keeps_last_successful_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "site.py").write_text("# test entry\n", encoding="utf-8")
    _FakeWatcher.instances.clear()

    calls = 0

    def fake_load(project_root: Path, entry_path: Path) -> BuildPlan:
        nonlocal calls
        del project_root, entry_path
        calls += 1
        if calls == 1:
            return _page_plan("<html><body>stable</body></html>")
        raise _ProjectPlanLoadError("broken rebuild")

    monkeypatch.setattr(
        "pypagekit.cli.commands.serve._load_project_plan",
        fake_load,
    )
    monkeypatch.setattr(
        "pypagekit.cli.commands.serve.DevelopmentWatcher",
        _FakeWatcher,
    )

    session = _FakeSession(tmp_path / "dist")

    def fake_create(
        self: object,
        config: DevelopmentServerConfig,
        *,
        live_reload: bool = False,
    ) -> _FakeSession:
        del self, config, live_reload
        return session

    monkeypatch.setattr(
        "pypagekit.cli.commands.serve.DevelopmentServer.create",
        fake_create,
    )

    result = runner.invoke(app, ["serve", "--watch"])

    assert result.exit_code == SUCCESS
    assert (tmp_path / "dist" / "index.html").read_text(encoding="utf-8") == (
        "<html><body>stable</body></html>"
    )
    assert session.reload_revisions == []
    assert "Rebuild failed: broken rebuild" in result.stderr
