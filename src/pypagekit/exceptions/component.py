"""Component composition and runtime exceptions."""

from .domain import PyPageKitError


class ComponentError(PyPageKitError):
    """Base exception for component composition failures."""


class InvalidComponentResultError(ComponentError):
    """Raised when Component.compose() does not return Content."""


class ComponentCycleError(ComponentError):
    """Raised when component composition references an active component."""


class ComponentResolutionDepthError(ComponentError):
    """Raised when component composition exceeds the runtime depth guard."""



class ComponentRegistryError(ComponentError):
    """Base exception for explicit component registry failures."""


class InvalidComponentNameError(ComponentRegistryError):
    """Raised when a registry name does not use the supported format."""


class InvalidComponentPropertyError(ComponentRegistryError):
    """Raised when a symbolic component property name is invalid."""


class DuplicateComponentRegistrationError(ComponentRegistryError):
    """Raised when an immutable registry already contains a component name."""


class UnknownComponentError(ComponentRegistryError):
    """Raised when a symbolic component name is absent from a registry."""


class InvalidRegisteredComponentError(ComponentRegistryError):
    """Raised when a registered factory does not return Component."""


class MissingComponentRegistryError(ComponentRegistryError):
    """Raised when ComponentRef resolution requires a registry but none exists."""
