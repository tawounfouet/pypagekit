"""Local static development server command."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath
from threading import Thread
from typing import Annotated, Any

import typer

from pypagekit import Asset, Page, Route
from pypagekit.build import (
    AssetBuildEntry,
    BuildPlan,
    FilesystemWriter,
    PageBuildEntry,
    build_manifest,
)
from pypagekit.development import (
    DevelopmentServer,
    DevelopmentServerConfig,
    DevelopmentServerError,
    DevelopmentWatcher,
)
from pypagekit.exceptions import PyPageKitError

from ..console import console, error_console
from ..exit_codes import EXECUTION_ERROR

_DEFAULT_WATCH_IGNORES = (
    PurePosixPath(".git"),
    PurePosixPath(".mypy_cache"),
    PurePosixPath(".pytest_cache"),
    PurePosixPath(".ruff_cache"),
    PurePosixPath(".venv"),
    PurePosixPath("__pycache__"),
)


class _ProjectPlanLoadError(RuntimeError):
    """Raised when watch-mode project code cannot produce a valid BuildPlan."""


def serve_command(
    root: Annotated[
        Path,
        typer.Argument(
            help="Static output directory to serve.",
        ),
    ] = Path("dist"),
    host: Annotated[
        str,
        typer.Option(
            "--host",
            help="Hostname or IPv4 address to bind.",
        ),
    ] = "127.0.0.1",
    port: Annotated[
        int,
        typer.Option(
            "--port",
            "-p",
            min=1,
            max=65535,
            help="TCP port to bind.",
        ),
    ] = 8000,
    watch: Annotated[
        bool,
        typer.Option(
            "--watch",
            help="Watch the current project and rebuild before browser live reload.",
        ),
    ] = False,
    entry: Annotated[
        Path,
        typer.Option(
            "--entry",
            help="Project entry file used by --watch. Must expose module-level 'site'.",
        ),
    ] = Path("site.py"),
    poll_interval: Annotated[
        float,
        typer.Option(
            "--poll-interval",
            min=0.01,
            help="Filesystem polling interval in seconds for --watch.",
        ),
    ] = 0.1,
    debounce_interval: Annotated[
        float,
        typer.Option(
            "--debounce-interval",
            min=0.0,
            help="Filesystem settle interval in seconds for --watch.",
        ),
    ] = 0.05,
) -> None:
    """Serve a generated static directory for local development."""

    if watch:
        _serve_with_watch(
            root=root,
            host=host,
            port=port,
            entry=entry,
            poll_interval=poll_interval,
            debounce_interval=debounce_interval,
        )
        return

    try:
        config = DevelopmentServerConfig(
            root=root,
            host=host,
            port=port,
        )
        with DevelopmentServer().create(config) as session:
            console.print(
                f"Serving {session.info.root} at {session.info.url} (Press Ctrl+C to stop)"
            )
            try:
                session.serve_forever()
            except KeyboardInterrupt:
                console.print("Development server stopped.")
    except DevelopmentServerError as exc:
        error_console.print(f"Development server failed: {exc}")
        raise typer.Exit(code=EXECUTION_ERROR) from exc


def _serve_with_watch(
    *,
    root: Path,
    host: str,
    port: int,
    entry: Path,
    poll_interval: float,
    debounce_interval: float,
) -> None:
    project_root = Path.cwd().resolve()
    output_root = _absolute_without_resolving_symlinks(root)
    writer = FilesystemWriter()

    try:
        entry_path = _validated_project_entry(project_root, entry)
        ignored_paths = _watch_ignored_paths(project_root, output_root)
        watcher = DevelopmentWatcher(
            project_root,
            ignored_paths=ignored_paths,
        )

        plan = _load_project_plan(project_root, entry_path)
        writer.write(plan, output_root, overwrite=True)
        previous_manifest = build_manifest(plan)
        source_snapshot = watcher.snapshot()

        config = DevelopmentServerConfig(
            root=output_root,
            host=host,
            port=port,
        )
        with DevelopmentServer().create(config, live_reload=True) as session:
            server_thread = Thread(
                target=session.serve_forever,
                name="pypagekit-development-server",
                daemon=True,
            )
            server_thread.start()
            console.print(
                f"Serving {session.info.root} at {session.info.url} "
                f"with watch + live reload (Press Ctrl+C to stop)"
            )

            try:
                while True:
                    batch = watcher.wait_for_changes(
                        source_snapshot,
                        poll_interval=poll_interval,
                        debounce_interval=debounce_interval,
                        timeout=0.5,
                    )
                    if batch is None:
                        if not server_thread.is_alive():
                            raise DevelopmentServerError(
                                "Development server stopped unexpectedly."
                            )
                        continue

                    source_snapshot = batch.current

                    try:
                        next_plan = _load_project_plan(project_root, entry_path)
                        result = writer.write_incremental(
                            next_plan,
                            previous_manifest,
                            output_root,
                        )
                    except (_ProjectPlanLoadError, PyPageKitError) as exc:
                        error_console.print(f"Rebuild failed: {exc}")
                        continue

                    previous_manifest = result.manifest
                    revision = session.notify_reload()
                    console.print(
                        "Rebuilt "
                        f"{len(result.written_files)} file(s), "
                        f"removed {len(result.removed_files)} file(s) "
                        f"(reload revision {revision})."
                    )
            except KeyboardInterrupt:
                console.print("Development server stopped.")
            finally:
                session.shutdown()
                server_thread.join(timeout=2)
    except (_ProjectPlanLoadError, PyPageKitError, OSError) as exc:
        error_console.print(f"Development watch failed: {exc}")
        raise typer.Exit(code=EXECUTION_ERROR) from exc


def _load_project_plan(
    project_root: Path,
    entry_path: Path,
) -> BuildPlan:
    environment = os.environ.copy()
    environment["PYTHONDONTWRITEBYTECODE"] = "1"

    try:
        completed = subprocess.run(
            [
                sys.executable,
                "-m",
                "pypagekit.development._project_plan",
                str(entry_path),
            ],
            cwd=project_root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except OSError as exc:
        raise _ProjectPlanLoadError(
            f"Unable to start a fresh Python process for '{entry_path.name}'."
        ) from exc

    if completed.returncode != 0:
        details = completed.stderr.strip()
        if details:
            raise _ProjectPlanLoadError(
                f"Project entry '{entry_path.name}' failed:\n{details}"
            )
        raise _ProjectPlanLoadError(
            f"Project entry '{entry_path.name}' failed with exit code "
            f"{completed.returncode}."
        )

    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise _ProjectPlanLoadError(
            f"Project entry '{entry_path.name}' returned an invalid build-plan payload."
        ) from exc

    try:
        return _decode_project_plan(payload)
    except (KeyError, TypeError, ValueError, PyPageKitError) as exc:
        raise _ProjectPlanLoadError(
            f"Project entry '{entry_path.name}' returned an invalid build plan."
        ) from exc


def _decode_project_plan(payload: Any) -> BuildPlan:
    if not isinstance(payload, dict):
        raise TypeError("Build-plan payload must be an object.")

    raw_pages = payload["pages"]
    raw_assets = payload["assets"]
    if not isinstance(raw_pages, list) or not isinstance(raw_assets, list):
        raise TypeError("Build-plan pages and assets must be lists.")

    pages: list[PageBuildEntry] = []
    for item in raw_pages:
        if not isinstance(item, dict):
            raise TypeError("Build-plan page entries must be objects.")

        route_path = item["route"]
        target = item["target"]
        content = item["content"]
        if not all(isinstance(value, str) for value in (route_path, target, content)):
            raise TypeError("Build-plan page values must be strings.")

        pages.append(
            PageBuildEntry(
                Route(route_path, Page("Development watch build")),
                PurePosixPath(target),
                content,
            )
        )

    assets: list[AssetBuildEntry] = []
    for item in raw_assets:
        if not isinstance(item, dict):
            raise TypeError("Build-plan asset entries must be objects.")

        source = item["source"]
        target = item["target"]
        if not isinstance(source, str) or not isinstance(target, str):
            raise TypeError("Build-plan asset values must be strings.")

        assets.append(
            AssetBuildEntry(
                Asset(
                    Path(source),
                    PurePosixPath(target),
                )
            )
        )

    return BuildPlan(pages, assets)


def _validated_project_entry(
    project_root: Path,
    entry: Path,
) -> Path:
    if not isinstance(entry, Path):
        raise TypeError("Watch project entry must be a pathlib.Path.")

    candidate = entry if entry.is_absolute() else project_root / entry
    candidate = candidate.absolute()

    try:
        relative = candidate.relative_to(project_root)
    except ValueError as exc:
        raise _ProjectPlanLoadError(
            "Watch project entry must remain inside the current project root."
        ) from exc

    cursor = project_root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink():
            raise _ProjectPlanLoadError(
                f"Watch project entry path '{cursor}' must not traverse a symlink."
            )

    if not candidate.exists():
        raise _ProjectPlanLoadError(
            f"Watch project entry '{candidate}' does not exist."
        )
    if not candidate.is_file():
        raise _ProjectPlanLoadError(
            f"Watch project entry '{candidate}' must be a regular file."
        )

    return candidate


def _watch_ignored_paths(
    project_root: Path,
    output_root: Path,
) -> tuple[PurePosixPath, ...]:
    ignored = list(_DEFAULT_WATCH_IGNORES)

    try:
        output_relative = output_root.relative_to(project_root)
    except ValueError:
        output_relative = None

    if output_relative is not None:
        if not output_relative.parts:
            raise _ProjectPlanLoadError(
                "Watch output root must not be the project root itself."
            )
        ignored.append(PurePosixPath(*output_relative.parts))

    return tuple(ignored)


def _absolute_without_resolving_symlinks(path: Path) -> Path:
    if not isinstance(path, Path):
        raise TypeError("Development output root must be a pathlib.Path.")
    return path if path.is_absolute() else (Path.cwd() / path).absolute()


__all__ = ["serve_command"]
