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


def test_release_workflow_requires_explicit_tag_or_release_branch() -> None:
    content = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert 'tags:\n      - "v*"' in content
    assert 'branches:\n      - "release/v*"' in content
    assert "workflow_dispatch" not in content
    assert "Prepare release tag" in content
    assert 'expected_branch="release/$tag"' in content
    assert "Existing tag $tag points to" in content
    assert "Verify stable tag matches source version" in content
    assert 're.fullmatch(r"v\\d+\\.\\d+\\.\\d+", tag)' in content


def test_release_workflow_uses_least_privilege_trusted_publishing() -> None:
    content = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert "environment:\n      name: pypi" in content
    assert "id-token: write" in content
    assert "pypa/gh-action-pypi-publish@release/v1" in content
    assert "PYPI_TOKEN" not in content
    assert "password:" not in content


def test_release_workflow_publishes_only_after_distribution_qualification() -> None:
    content = RELEASE_WORKFLOW_PATH.read_text(encoding="utf-8")

    assert (
        "github-release:\n    name: Publish GitHub Release\n"
        "    needs: [prepare, qualify]" in content
    )
    assert "pypi:\n    name: Publish to PyPI\n    needs: [prepare, github-release]" in content
    assert "actions/upload-artifact@v4" in content
    assert "actions/download-artifact@v4" in content
    assert 'gh release upload "$tag" dist/* --clobber' in content
