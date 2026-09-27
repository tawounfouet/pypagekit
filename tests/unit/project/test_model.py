from dataclasses import FrozenInstanceError
from pathlib import Path, PurePosixPath

import pytest

from pypagekit.project import ProjectFile, ProjectPathConflictError, ProjectPlan


def test_project_file_preserves_target_and_content() -> None:
    project_file = ProjectFile(PurePosixPath("site.py"), "print('hello')\n")

    assert project_file.target == PurePosixPath("site.py")
    assert project_file.content == "print('hello')\n"


@pytest.mark.parametrize(
    "target",
    [
        PurePosixPath("/site.py"),
        PurePosixPath("."),
        PurePosixPath("../site.py"),
    ],
)
def test_project_file_rejects_unsafe_target(target: PurePosixPath) -> None:
    with pytest.raises(ProjectPathConflictError):
        ProjectFile(target, "content")


def test_project_file_target_requires_pure_posix_path() -> None:
    with pytest.raises(TypeError, match="PurePosixPath"):
        ProjectFile(Path("site.py"), "content")  # type: ignore[arg-type]


def test_project_plan_preserves_order() -> None:
    first = ProjectFile(PurePosixPath("README.md"), "readme")
    second = ProjectFile(PurePosixPath("site.py"), "site")

    plan = ProjectPlan(Path("demo"), "demo", [first, second])

    assert plan.files == (first, second)
    assert plan.targets == (
        PurePosixPath("README.md"),
        PurePosixPath("site.py"),
    )


def test_project_plan_rejects_duplicate_targets() -> None:
    with pytest.raises(ProjectPathConflictError, match="appears more than once"):
        ProjectPlan(
            Path("demo"),
            "demo",
            [
                ProjectFile(PurePosixPath("site.py"), "one"),
                ProjectFile(PurePosixPath("site.py"), "two"),
            ],
        )


def test_project_plan_is_immutable() -> None:
    plan = ProjectPlan(Path("demo"), "demo", ())

    with pytest.raises(FrozenInstanceError):
        plan.project_name = "changed"  # type: ignore[misc]
