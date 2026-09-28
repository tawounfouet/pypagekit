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


class BuildRenderError(BuildError):
    """Raised when a renderer fails unexpectedly while planning a route."""


class InvalidBuildPlanError(BuildError):
    """Raised when a planner does not return a BuildPlan."""


class BuildManifestError(BuildError):
    """Base exception for build fingerprint and manifest failures."""


class InvalidBuildFingerprintError(BuildManifestError):
    """Raised when a build fingerprint is malformed or unsupported."""


class InvalidBuildManifestError(BuildManifestError):
    """Raised when a build manifest declaration is invalid."""


class BuildManifestSourceError(BuildManifestError):
    """Raised when an asset source cannot be fingerprinted deterministically."""


class FilesystemOutputError(BuildError):
    """Base exception for filesystem materialization failures."""


class IncrementalOutputDriftError(FilesystemOutputError):
    """Raised when tracked output no longer matches the previous build manifest."""


class InvalidOutputRootError(FilesystemOutputError):
    """Raised when an output root is not a usable directory path."""


class ExistingOutputError(FilesystemOutputError):
    """Raised when a target file exists and overwrite is disabled."""


class OutputPathConflictError(FilesystemOutputError):
    """Raised when existing filesystem structure conflicts with the plan."""


class OutputSymlinkError(FilesystemOutputError):
    """Raised when an output path would traverse or replace a symlink."""


class InvalidAssetSourceForOutputError(FilesystemOutputError):
    """Raised when an asset source cannot be copied as a regular file."""


class AssetSourceOutputConflictError(FilesystemOutputError):
    """Raised when an asset source is also its planned destination."""


class FilesystemWriteError(FilesystemOutputError):
    """Raised when filesystem materialization fails after successful preflight."""


class FilesystemRollbackError(FilesystemWriteError):
    """Raised when filesystem state cannot be restored after a write failure."""
