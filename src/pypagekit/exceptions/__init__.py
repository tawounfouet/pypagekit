"""Public PyPageKit exception hierarchy."""

from .domain import (
    DomainError,
    InvalidHeadingLevelError,
    InvalidPageContentError,
    InvalidPageLanguageError,
    InvalidPageTitleError,
    PyPageKitError,
    ValidationError,
)

__all__ = [
    "DomainError",
    "InvalidHeadingLevelError",
    "InvalidPageContentError",
    "InvalidPageLanguageError",
    "InvalidPageTitleError",
    "PyPageKitError",
    "ValidationError",
]
