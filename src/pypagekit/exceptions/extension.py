"""Extension registry exceptions."""

from .domain import PyPageKitError


class ExtensionError(PyPageKitError):
    """Base exception for extension contract failures."""


class InvalidExtensionDescriptorError(ExtensionError):
    """Raised when extension metadata is invalid."""


class InvalidExtensionIdError(InvalidExtensionDescriptorError):
    """Raised when an extension ID is not stable and portable."""


class DuplicateComponentContributionError(ExtensionError):
    """Raised when component extensions contribute the same symbolic name."""


class DuplicateExtensionRegistrationError(ExtensionError):
    """Raised when an extension ID is already registered."""


class UnknownExtensionError(ExtensionError):
    """Raised when an extension ID is absent from a registry."""


class InvalidBuildPlannerExtensionError(ExtensionError):
    """Raised when a build planner extension does not produce a planner."""


class InvalidRendererExtensionError(ExtensionError):
    """Raised when a renderer extension does not produce a renderer."""


__all__ = [
    "DuplicateComponentContributionError",
    "DuplicateExtensionRegistrationError",
    "ExtensionError",
    "InvalidExtensionDescriptorError",
    "InvalidBuildPlannerExtensionError",
    "InvalidExtensionIdError",
    "InvalidRendererExtensionError",
    "UnknownExtensionError",
]
