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
from .rendering import (
    InvalidHtmlAttributeNameError,
    InvalidHtmlTagError,
    RenderingError,
    SecurityError,
    SerializationError,
    UnsafeUrlError,
    UnsupportedAttributeValueError,
    UnsupportedNodeError,
)

__all__ = [
    "DomainError",
    "InvalidContainerChildError",
    "InvalidHeadingLevelError",
    "InvalidHtmlAttributeNameError",
    "InvalidHtmlTagError",
    "InvalidImageSourceError",
    "InvalidLinkHrefError",
    "InvalidPageContentError",
    "InvalidPageLanguageError",
    "InvalidPageTitleError",
    "PyPageKitError",
    "RenderingError",
    "SecurityError",
    "SerializationError",
    "UnsafeUrlError",
    "UnsupportedAttributeValueError",
    "UnsupportedNodeError",
    "ValidationError",
]
