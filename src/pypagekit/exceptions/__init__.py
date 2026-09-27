"""Public PyPageKit exception hierarchy."""

from .domain import (
    DomainError,
    InvalidContainerChildError,
    InvalidHeadingLevelError,
    InvalidPageContentError,
    InvalidPageLanguageError,
    InvalidPageTitleError,
    PyPageKitError,
    ValidationError,
)

__all__ = [
    "DomainError",
    "InvalidContainerChildError",
    "InvalidHeadingLevelError",
    "InvalidPageContentError",
    "InvalidPageLanguageError",
    "InvalidPageTitleError",
    "PyPageKitError",
    "ValidationError",
]
