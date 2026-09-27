from pathlib import Path

from pypagekit.diagnostics import (
    DiagnosticCheck,
    DiagnosticReport,
    DiagnosticStatus,
    ProjectInspection,
)


def test_diagnostic_report_projects_status_groups() -> None:
    passed = DiagnosticCheck("a", "A", DiagnosticStatus.PASS, "ok")
    warning = DiagnosticCheck("b", "B", DiagnosticStatus.WARNING, "warn")
    failed = DiagnosticCheck("c", "C", DiagnosticStatus.FAIL, "bad")
    report = DiagnosticReport((passed, warning, failed))

    assert report.passed == (passed,)
    assert report.warnings == (warning,)
    assert report.failures == (failed,)
    assert not report.healthy


def test_project_inspection_is_immutable_value_data() -> None:
    inspection = ProjectInspection(
        root=Path("/project"),
        project_name="demo",
        python_version="3.13.0",
        pypagekit_version="0.6.0b2",
        pyproject_present=True,
        site_present=True,
        output_root=Path("/project/dist"),
        output_present=True,
        index_present=True,
    )

    assert inspection.project_name == "demo"
    assert inspection.index_present
