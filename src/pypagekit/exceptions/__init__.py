"""Public PyPageKit exception hierarchy."""

from .domain import (
    DomainError,
    InvalidContainerChildError,
    InvalidHeadingLevelError,
    InvalidImageSourceError,
    InvalidLinkHrefError,
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
    "InvalidImageSourceError",
    "InvalidLinkHrefError",
    "InvalidPageContentError",
    "InvalidPageLanguageError",
    "InvalidPageTitleError",
    "PyPageKitError",
    "ValidationError",
]
