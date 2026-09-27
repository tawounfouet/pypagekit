"""Rendering and HTML serialization exceptions."""

from .domain import PyPageKitError


class RenderingError(PyPageKitError):
    """Base exception for failures while producing a representation."""


class UnsupportedNodeError(RenderingError):
    """Raised when a renderer does not support a domain node type."""


class SerializationError(RenderingError):
    """Base exception for invalid HTML serialization operations."""


class InvalidHtmlTagError(SerializationError):
    """Raised when an HTML tag name or element kind is invalid."""


class InvalidHtmlAttributeNameError(SerializationError):
    """Raised when an HTML attribute name is structurally invalid."""


class UnsupportedAttributeValueError(SerializationError):
    """Raised when an attribute value cannot be serialized safely."""
