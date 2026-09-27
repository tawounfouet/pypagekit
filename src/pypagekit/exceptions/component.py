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
