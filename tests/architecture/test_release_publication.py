import tomllib
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
PYPROJECT_PATH = REPOSITORY_ROOT / "pyproject.toml"
RELEASE_WORKFLOW_PATH = REPOSITORY_ROOT / ".github/workflows/release.yml"


def test_distribution_metadata_exposes_canonical_project_urls() -> None:
    with PYPROJECT_PATH.open("rb") as stream:
        project = tomllib.load(stream)["project"]

    urls = project["urls"]
    assert urls == {
        "Homepage": "https://github.com/tawounfouet/pypagekit",
        "Repository": "https://github.com/tawounfouet/pypagekit",
        "Issues": "https://github.com/tawounfouet/pypagekit/issues",
        "Changelog": "https://github.com/tawounfouet/pypagekit/blob/main/CHANGELOG.md",
    }


def test_release_workflow_is_tag_driven_and_not_manually_dispatchable() -> None:
    content = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert 'tags:\n      - "v*"' in content
    assert "workflow_dispatch" not in content
    assert "Verify stable tag matches package version" in content
    assert r're.fullmatch(r"v\\d+\\.\\d+\\.\\d+", tag)' in content


def test_release_workflow_uses_least_privilege_trusted_publishing() -> None:
    content = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "environment:\n      name: pypi" in content
    assert "id-token: write" in content
    assert "pypa/gh-action-pypi-publish@release/v1" in content
    assert "PYPI_TOKEN" not in content
    assert "password:" not in content


def test_release_workflow_publishes_only_after_distribution_qualification() -> None:
    content = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "github-release:\n    name: Publish GitHub Release\n    needs: qualify" in content
    assert "pypi:\n    name: Publish to PyPI\n    needs: github-release" in content
    assert "actions/upload-artifact@v4" in content
    assert "actions/download-artifact@v4" in content
    assert 'gh release upload "$tag" dist/* --clobber' in content
