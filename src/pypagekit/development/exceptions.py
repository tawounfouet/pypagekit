"""Development server exceptions."""

from pypagekit.exceptions import PyPageKitError


class DevelopmentServerError(PyPageKitError):
    """Base exception for local development server failures."""


class InvalidDevelopmentRootError(DevelopmentServerError):
    """Raised when the static root cannot be served safely."""


class InvalidDevelopmentHostError(DevelopmentServerError):
    """Raised when a bind host is invalid."""


class InvalidDevelopmentPortError(DevelopmentServerError):
    """Raised when a bind port is invalid."""


class DevelopmentServerBindError(DevelopmentServerError):
    """Raised when the local HTTP server cannot bind its address."""


__all__ = [
    "DevelopmentServerBindError",
    "DevelopmentServerError",
    "InvalidDevelopmentHostError",
    "InvalidDevelopmentPortError",
    "InvalidDevelopmentRootError",
]
