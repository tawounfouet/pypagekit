from pathlib import Path

import pytest

from pypagekit.project import ProjectScaffolder, ProjectSymlinkError


def test_scaffold_cannot_traverse_symlinked_parent(tmp_path: Path) -> None:
    outside = tmp_path / "outside"
    outside.mkdir()
    link = tmp_path / "projects"
    link.symlink_to(outside, target_is_directory=True)

    with pytest.raises(ProjectSymlinkError):
        ProjectScaffolder().scaffold(link / "demo")

    assert list(outside.iterdir()) == []


def test_force_never_follows_target_symlink(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    target.mkdir()
    outside = tmp_path / "outside.md"
    outside.write_text("protected", encoding="utf-8")
    (target / "README.md").symlink_to(outside)

    with pytest.raises(ProjectSymlinkError):
        ProjectScaffolder().scaffold(target, force=True)

    assert outside.read_text(encoding="utf-8") == "protected"
