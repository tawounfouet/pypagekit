import subprocess
import sys


def test_python_module_entrypoint_reports_version() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pypagekit", "--version"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert result.stdout.strip().startswith("PyPageKit ")
    assert result.stderr == ""


def test_python_module_entrypoint_help_succeeds() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "pypagekit", "--help"],
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "Python-first structured page and static site framework." in result.stdout
