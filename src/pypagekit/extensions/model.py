"""Immutable extension contract models."""

import re
from collections.abc import Callable
from dataclasses import dataclass

from pypagekit.exceptions import InvalidExtensionDescriptorError, InvalidExtensionIdError
from pypagekit.rendering import Renderer

_EXTENSION_ID_RE = re.compile(r"[a-z][a-z0-9]*(?:[.-][a-z0-9]+)*\Z")

RendererFactory = Callable[[], Renderer]


def validate_extension_id(extension_id: str) -> None:
    """Validate a stable namespaced extension identifier."""

    if not isinstance(extension_id, str):
        raise TypeError("Extension ID must be a string.")
    if not _EXTENSION_ID_RE.fullmatch(extension_id):
        raise InvalidExtensionIdError(
            "Extension ID must use lowercase ASCII letters/digits with '.' or '-' separators."
        )


@dataclass(frozen=True, slots=True)
class ExtensionDescriptor:
    """Stable metadata identifying one extension contribution."""

    extension_id: str
    name: str
    version: str

    def __post_init__(self) -> None:
        validate_extension_id(self.extension_id)
        _validate_non_empty_literal(self.name, field_name="Extension name")
        _validate_non_empty_literal(self.version, field_name="Extension version")


@dataclass(frozen=True, slots=True)
class RendererExtension:
    """One renderer contribution backed by an explicit factory."""

    descriptor: ExtensionDescriptor
    factory: RendererFactory

    def __post_init__(self) -> None:
        if not isinstance(self.descriptor, ExtensionDescriptor):
            raise TypeError("Renderer extension descriptor must be an ExtensionDescriptor.")
        if not callable(self.factory):
            raise TypeError("Renderer extension factory must be callable.")


def _validate_non_empty_literal(value: str, *, field_name: str) -> None:
    if not isinstance(value, str):
        raise TypeError(f"{field_name} must be a string.")
    if not value or value.strip() != value:
        raise InvalidExtensionDescriptorError(
            f"{field_name} must be non-empty and must not contain surrounding whitespace."
        )


__all__ = [
    "ExtensionDescriptor",
    "RendererExtension",
    "RendererFactory",
    "validate_extension_id",
]
