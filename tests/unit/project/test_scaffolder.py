from pathlib import Path, PurePosixPath

import pytest

from pypagekit import __version__
from pypagekit.project import (
    ExistingProjectFileError,
    InvalidProjectNameError,
    InvalidProjectTargetError,
    ProjectScaffolder,
    ProjectSymlinkError,
    normalize_project_name,
    pypagekit_requirement,
)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("my-site", "my-site"),
        ("My Site", "my-site"),
        ("demo_project", "demo-project"),
        ("  Demo...Project  ", "demo-project"),
    ],
)
def test_project_name_normalization(raw: str, expected: str) -> None:
    assert normalize_project_name(raw) == expected


def test_project_name_normalization_rejects_empty_semantics() -> None:
    with pytest.raises(InvalidProjectNameError):
        normalize_project_name("___")


def test_requirement_tracks_current_cli_release_line() -> None:
    assert pypagekit_requirement().startswith(f"pypagekit>={__version__},")
    assert pypagekit_requirement().endswith("<0.7")


def test_plan_is_deterministic_and_performs_no_write(tmp_path: Path) -> None:
    target = tmp_path / "My Project"

    plan = ProjectScaffolder().plan(target)

    assert not target.exists()
    assert plan.target_root == target
    assert plan.project_name == "my-project"
    assert plan.targets == (
        PurePosixPath(".gitignore"),
        PurePosixPath("README.md"),
        PurePosixPath("pyproject.toml"),
        PurePosixPath("site.py"),
    )


def test_plan_supports_explicit_project_name(tmp_path: Path) -> None:
    plan = ProjectScaffolder().plan(
        tmp_path / "directory-name",
        project_name="Custom Project",
    )

    assert plan.project_name == "custom-project"


def test_scaffold_creates_expected_files(tmp_path: Path) -> None:
    target = tmp_path / "demo"

    result = ProjectScaffolder().scaffold(target)

    assert result.target_root == target
    assert result.project_name == "demo"
    assert result.files == (
        target / ".gitignore",
        target / "README.md",
        target / "pyproject.toml",
        target / "site.py",
    )
    assert all(path.is_file() for path in result.files)
    assert "pypagekit>=" in (target / "pyproject.toml").read_text(encoding="utf-8")
    assert "StaticSiteGenerator" in (target / "site.py").read_text(encoding="utf-8")


def test_scaffold_preserves_unplanned_existing_files(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    target.mkdir()
    unplanned = target / "notes.txt"
    unplanned.write_text("keep", encoding="utf-8")

    ProjectScaffolder().scaffold(target)

    assert unplanned.read_text(encoding="utf-8") == "keep"


def test_existing_managed_file_is_rejected_before_any_write(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    target.mkdir()
    existing = target / "site.py"
    existing.write_text("existing", encoding="utf-8")

    with pytest.raises(ExistingProjectFileError):
        ProjectScaffolder().scaffold(target)

    assert existing.read_text(encoding="utf-8") == "existing"
    assert not (target / "README.md").exists()
    assert not (target / "pyproject.toml").exists()


def test_force_replaces_managed_regular_files(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    target.mkdir()
    existing = target / "site.py"
    existing.write_text("old", encoding="utf-8")

    ProjectScaffolder().scaffold(target, force=True)

    assert "StaticSiteGenerator" in existing.read_text(encoding="utf-8")


def test_target_root_existing_file_is_rejected(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    target.write_text("file", encoding="utf-8")

    with pytest.raises(InvalidProjectTargetError):
        ProjectScaffolder().scaffold(target)


def test_target_root_symlink_is_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    target = tmp_path / "demo"
    target.symlink_to(real, target_is_directory=True)

    with pytest.raises(ProjectSymlinkError):
        ProjectScaffolder().scaffold(target)


def test_symlinked_target_parent_is_rejected(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    linked_parent = tmp_path / "linked"
    linked_parent.symlink_to(real, target_is_directory=True)
    target = linked_parent / "demo"

    with pytest.raises(ProjectSymlinkError):
        ProjectScaffolder().scaffold(target)

    assert not (real / "demo").exists()


def test_force_does_not_replace_symlinked_managed_file(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    target.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("protected", encoding="utf-8")
    (target / "site.py").symlink_to(outside)

    with pytest.raises(ProjectSymlinkError):
        ProjectScaffolder().scaffold(target, force=True)

    assert outside.read_text(encoding="utf-8") == "protected"
