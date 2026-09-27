import subprocess
import sys
import tomllib
from pathlib import Path

from pypagekit.project import ProjectScaffolder


def test_generated_project_metadata_is_valid_toml(tmp_path: Path) -> None:
    target = tmp_path / "Demo Project"

    ProjectScaffolder().scaffold(target)

    data = tomllib.loads((target / "pyproject.toml").read_text(encoding="utf-8"))

    assert data["project"]["name"] == "demo-project"
    assert data["project"]["version"] == "0.1.0"
    assert data["project"]["requires-python"] == ">=3.11"
    assert len(data["project"]["dependencies"]) == 1
    assert data["project"]["dependencies"][0].startswith("pypagekit>=")


def test_generated_site_is_immediately_executable(tmp_path: Path) -> None:
    target = tmp_path / "demo"
    ProjectScaffolder().scaffold(target)

    result = subprocess.run(
        [sys.executable, "site.py"],
        cwd=target,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "Generated 1 file(s) in dist" in result.stdout
    html = (target / "dist" / "index.html").read_text(encoding="utf-8")
    assert "<title>Home</title>" in html
    assert "<p>Welcome to your PyPageKit site.</p>" in html
