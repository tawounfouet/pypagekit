"""Build planning exceptions for PyPageKit."""

from .domain import PyPageKitError


class BuildError(PyPageKitError):
    """Base exception for build planning failures."""


class InvalidBuildInputError(BuildError):
    """Raised when a build planner receives an unsupported input object."""


class InvalidBuildTargetError(BuildError):
    """Raised when a planned output target is not portable or safe."""


class BuildTargetCollisionError(BuildError):
    """Raised when planned targets conflict as files or directories."""


class InvalidBuildContentError(BuildError):
    """Raised when a renderer does not produce string page content."""
