"""Exceptions raised by developer diagnostics services."""


class DiagnosticsError(Exception):
    """Base error for diagnostics and inspection failures."""


class InvalidInspectionRootError(DiagnosticsError):
    """Raised when a project inspection root is unusable."""


__all__ = [
    "DiagnosticsError",
    "InvalidInspectionRootError",
]
