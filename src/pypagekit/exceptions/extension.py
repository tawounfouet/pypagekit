"""Extension registry exceptions."""

from .domain import PyPageKitError


class ExtensionError(PyPageKitError):
    """Base exception for extension contract failures."""


class InvalidExtensionDescriptorError(ExtensionError):
    """Raised when extension metadata is invalid."""


class InvalidExtensionIdError(InvalidExtensionDescriptorError):
    """Raised when an extension ID is not stable and portable."""


class DuplicateExtensionRegistrationError(ExtensionError):
    """Raised when an extension ID is already registered."""


class UnknownExtensionError(ExtensionError):
    """Raised when an extension ID is absent from a registry."""


class InvalidRendererExtensionError(ExtensionError):
    """Raised when a renderer extension does not produce a renderer."""


__all__ = [
    "DuplicateExtensionRegistrationError",
    "ExtensionError",
    "InvalidExtensionDescriptorError",
    "InvalidExtensionIdError",
    "InvalidRendererExtensionError",
    "UnknownExtensionError",
]
