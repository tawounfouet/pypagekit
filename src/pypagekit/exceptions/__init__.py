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
    SerializationError,
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
    "SerializationError",
    "UnsupportedAttributeValueError",
    "UnsupportedNodeError",
    "ValidationError",
]
