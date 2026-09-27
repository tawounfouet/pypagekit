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


class PluginDiscoveryError(ExtensionError):
    """Base exception for installed plugin discovery failures."""


class InvalidPluginEntryPointError(PluginDiscoveryError):
    """Raised when a plugin entry point violates the discovery contract."""


class PluginEntryPointLoadError(PluginDiscoveryError):
    """Raised when an entry point target cannot be loaded."""


class PluginProviderError(PluginDiscoveryError):
    """Raised when an entry point provider fails while creating an extension."""


class PluginLifecycleError(ExtensionError):
    """Base exception for explicit plugin lifecycle failures."""


class InvalidPluginLifecycleTransitionError(PluginLifecycleError):
    """Raised when a lifecycle operation is requested from an invalid state."""


class PluginActivationError(PluginLifecycleError):
    """Raised when a plugin cannot be activated or deactivated."""


class UnknownPluginError(PluginActivationError):
    """Raised when a lifecycle operation references an unknown plugin ID."""


__all__ = [
    "DuplicateComponentContributionError",
    "DuplicateExtensionRegistrationError",
    "ExtensionError",
    "InvalidBuildPlannerExtensionError",
    "InvalidExtensionDescriptorError",
    "InvalidExtensionIdError",
    "InvalidPluginEntryPointError",
    "InvalidPluginLifecycleTransitionError",
    "InvalidRendererExtensionError",
    "PluginActivationError",
    "PluginDiscoveryError",
    "PluginEntryPointLoadError",
    "PluginLifecycleError",
    "PluginProviderError",
    "UnknownExtensionError",
    "UnknownPluginError",
]
