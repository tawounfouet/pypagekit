"""Explicit immutable registry for renderer extensions."""

from collections.abc import Iterable
from dataclasses import dataclass
from typing import cast

from pypagekit.exceptions import (
    DuplicateExtensionRegistrationError,
    InvalidRendererExtensionError,
    UnknownExtensionError,
)
from pypagekit.rendering import Renderer

from .model import RendererExtension, validate_extension_id


@dataclass(frozen=True, slots=True, init=False)
class RendererRegistry:
    """Immutable collection of explicitly supplied renderer extensions."""

    entries: tuple[RendererExtension, ...]

    def __init__(self, extensions: Iterable[RendererExtension] | None = None) -> None:
        if extensions is None:
            normalized: tuple[RendererExtension, ...] = ()
        else:
            collected: list[RendererExtension] = []
            seen: set[str] = set()
            for extension in extensions:
                if not isinstance(extension, RendererExtension):
                    raise TypeError(
                        "Renderer registry entries must be RendererExtension objects."
                    )
                extension_id = extension.descriptor.extension_id
                if extension_id in seen:
                    raise DuplicateExtensionRegistrationError(
                        f"Renderer extension '{extension_id}' is already registered."
                    )
                seen.add(extension_id)
                collected.append(extension)
            normalized = tuple(
                sorted(collected, key=lambda item: item.descriptor.extension_id)
            )

        object.__setattr__(self, "entries", normalized)

    @property
    def ids(self) -> tuple[str, ...]:
        """Return registered extension IDs in deterministic order."""

        return tuple(extension.descriptor.extension_id for extension in self.entries)

    def contains(self, extension_id: str) -> bool:
        """Return whether a renderer extension is registered."""

        validate_extension_id(extension_id)
        return extension_id in self.ids

    def register(self, extension: RendererExtension) -> "RendererRegistry":
        """Return a new registry containing one additional renderer extension."""

        if not isinstance(extension, RendererExtension):
            raise TypeError("Renderer registry can register only RendererExtension objects.")
        extension_id = extension.descriptor.extension_id
        if self.contains(extension_id):
            raise DuplicateExtensionRegistrationError(
                f"Renderer extension '{extension_id}' is already registered."
            )
        return RendererRegistry((*self.entries, extension))

    def extension(self, extension_id: str) -> RendererExtension:
        """Return the renderer extension registered under an ID."""

        validate_extension_id(extension_id)
        for extension in self.entries:
            if extension.descriptor.extension_id == extension_id:
                return extension
        raise UnknownExtensionError(f"Unknown renderer extension: '{extension_id}'.")

    def create(self, extension_id: str) -> Renderer:
        """Instantiate and validate the renderer registered under an ID."""

        extension = self.extension(extension_id)
        renderer = extension.factory()
        render_method = getattr(renderer, "render", None)
        if not callable(render_method):
            raise InvalidRendererExtensionError(
                f"Renderer extension '{extension_id}' must produce an object "
                "with a callable render() method."
            )
        return cast(Renderer, renderer)


__all__ = ["RendererRegistry"]
