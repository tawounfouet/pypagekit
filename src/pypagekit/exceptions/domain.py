"""Domain exceptions raised by PyPageKit."""


class PyPageKitError(Exception):
    """Base exception for all PyPageKit-specific failures."""


class DomainError(PyPageKitError):
    """Base exception for invalid domain operations or states."""


class ValidationError(DomainError):
    """Base exception for domain validation failures."""


class InvalidPageTitleError(ValidationError):
    """Raised when a page title is empty after normalization."""


class InvalidPageLanguageError(ValidationError):
    """Raised when a page language value is empty after normalization."""


class InvalidPageContentError(ValidationError):
    """Raised when a page contains an object that is not Content."""


class InvalidHeadingLevelError(ValidationError):
    """Raised when a heading level is outside the supported 1..6 range."""
