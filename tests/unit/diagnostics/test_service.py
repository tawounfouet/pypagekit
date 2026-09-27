from pathlib import Path

import pytest

from pypagekit.diagnostics import (
    DeveloperDiagnostics,
    DiagnosticStatus,
    InvalidInspectionRootError,
    ProjectInspector,
)


def _write_project(root: Path, *, with_output: bool = True) -> None:
    root.mkdir()
    (root / "pyproject.toml").write_text(
        '[project]\nname = "demo-site"\n',
        encoding="utf-8",
    )
    (root / "site.py").write_text("# demo\n", encoding="utf-8")
    if with_output:
        output = root / "dist"
        output.mkdir()
        (output / "index.html").write_text("<h1>Demo</h1>", encoding="utf-8")


def test_diagnostics_pass_for_complete_project(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    _write_project(root)

    report = DeveloperDiagnostics().run(root)

    assert report.healthy
    assert report.failures == ()
    by_code = {check.code: check for check in report.checks}
    assert by_code["project.metadata"].status is DiagnosticStatus.PASS
    assert by_code["output.index"].status is DiagnosticStatus.PASS


def test_missing_generated_output_is_warning_not_failure(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    _write_project(root, with_output=False)

    report = DeveloperDiagnostics().run(root)

    assert report.healthy
    assert {check.code for check in report.warnings} == {
        "output.directory",
        "output.index",
    }


def test_missing_project_files_make_diagnostics_unhealthy(tmp_path: Path) -> None:
    root = tmp_path / "empty"
    root.mkdir()

    report = DeveloperDiagnostics().run(root)

    assert not report.healthy
    failed_codes = {check.code for check in report.failures}
    assert "project.pyproject" in failed_codes
    assert "project.metadata" in failed_codes
    assert "project.site" in failed_codes


def test_inspector_reads_project_name_without_executing_site(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    _write_project(root)

    inspection = ProjectInspector().inspect(root)

    assert inspection.project_name == "demo-site"
    assert inspection.pyproject_present
    assert inspection.site_present
    assert inspection.output_present
    assert inspection.index_present


def test_inspector_reports_malformed_pyproject_as_metadata_error(tmp_path: Path) -> None:
    root = tmp_path / "demo"
    root.mkdir()
    (root / "pyproject.toml").write_text("[project\n", encoding="utf-8")

    inspection = ProjectInspector().inspect(root)

    assert inspection.project_name is None
    assert inspection.metadata_error is not None


def test_inspector_rejects_missing_root(tmp_path: Path) -> None:
    with pytest.raises(InvalidInspectionRootError, match="does not exist"):
        ProjectInspector().inspect(tmp_path / "missing")
