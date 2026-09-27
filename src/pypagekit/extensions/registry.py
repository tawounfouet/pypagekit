"""Explicit immutable registries for extension contributions."""

from collections.abc import Iterable
from dataclasses import dataclass, field

from pypagekit.build import BuildPlannerProtocol
from pypagekit.components import ComponentRegistry
from pypagekit.exceptions import (
    DuplicateComponentContributionError,
    DuplicateExtensionRegistrationError,
    ExtensionFactoryError,
    InvalidBuildPlannerExtensionError,
    InvalidRendererExtensionError,
    UnknownExtensionError,
)
from pypagekit.rendering import Renderer

from .model import (
    BuildPlannerExtension,
    ComponentExtension,
    RendererExtension,
    validate_extension_id,
)


@dataclass(frozen=True, slots=True, init=False)
class BuildPlannerRegistry:
    """Immutable collection of explicitly supplied build planner extensions."""

    entries: tuple[BuildPlannerExtension, ...]
    _ids: tuple[str, ...] = field(repr=False, compare=False)

    def __init__(self, extensions: Iterable[BuildPlannerExtension] | None = None) -> None:
        if extensions is None:
            normalized: tuple[BuildPlannerExtension, ...] = ()
        else:
            collected: list[BuildPlannerExtension] = []
            seen: set[str] = set()
            for extension in extensions:
                if not isinstance(extension, BuildPlannerExtension):
                    raise TypeError(
                        "Build planner registry entries must be BuildPlannerExtension objects."
                    )
                extension_id = extension.descriptor.extension_id
                if extension_id in seen:
                    raise DuplicateExtensionRegistrationError(
                        f"Build planner extension '{extension_id}' is already registered."
                    )
                seen.add(extension_id)
                collected.append(extension)
            normalized = tuple(sorted(collected, key=lambda item: item.descriptor.extension_id))

        object.__setattr__(self, "entries", normalized)
        object.__setattr__(
            self,
            "_ids",
            tuple(extension.descriptor.extension_id for extension in normalized),
        )

    @property
    def ids(self) -> tuple[str, ...]:
        """Return registered extension IDs in deterministic order."""

        return self._ids

    def contains(self, extension_id: str) -> bool:
        """Return whether a build planner extension is registered."""

        validate_extension_id(extension_id)
        return _sorted_string_index(self._ids, extension_id) is not None

    def register(self, extension: BuildPlannerExtension) -> "BuildPlannerRegistry":
        """Return a new registry containing one additional build planner extension."""

        if not isinstance(extension, BuildPlannerExtension):
            raise TypeError(
                "Build planner registry can register only BuildPlannerExtension objects."
            )
        extension_id = extension.descriptor.extension_id
        if self.contains(extension_id):
            raise DuplicateExtensionRegistrationError(
                f"Build planner extension '{extension_id}' is already registered."
            )
        return BuildPlannerRegistry((*self.entries, extension))

    def extension(self, extension_id: str) -> BuildPlannerExtension:
        """Return the build planner extension registered under an ID."""

        validate_extension_id(extension_id)
        index = _sorted_string_index(self._ids, extension_id)
        if index is not None:
            return self.entries[index]
        raise UnknownExtensionError(f"Unknown build planner extension: '{extension_id}'.")

    def create(self, extension_id: str) -> BuildPlannerProtocol:
        """Instantiate and validate the build planner registered under an ID."""

        extension = self.extension(extension_id)
        try:
            planner = extension.factory()
        except Exception as exc:
            raise ExtensionFactoryError(
                f"Build planner extension '{extension_id}' factory failed."
            ) from exc

        if not callable(getattr(planner, "plan", None)):
            raise InvalidBuildPlannerExtensionError(
                f"Build planner extension '{extension_id}' must produce an object "
                "with a callable plan() method."
            )
        return planner


@dataclass(frozen=True, slots=True, init=False)
class ComponentExtensionRegistry:
    """Immutable registry of component extension bundles."""

    entries: tuple[ComponentExtension, ...]
    _ids: tuple[str, ...] = field(repr=False, compare=False)
    _component_names: tuple[str, ...] = field(repr=False, compare=False)

    def __init__(self, extensions: Iterable[ComponentExtension] | None = None) -> None:
        if extensions is None:
            normalized: tuple[ComponentExtension, ...] = ()
        else:
            collected: list[ComponentExtension] = []
            seen_ids: set[str] = set()
            for extension in extensions:
                if not isinstance(extension, ComponentExtension):
                    raise TypeError(
                        "Component extension registry entries must be ComponentExtension objects."
                    )
                extension_id = extension.descriptor.extension_id
                if extension_id in seen_ids:
                    raise DuplicateExtensionRegistrationError(
                        f"Component extension '{extension_id}' is already registered."
                    )
                seen_ids.add(extension_id)
                collected.append(extension)

            normalized = tuple(sorted(collected, key=lambda item: item.descriptor.extension_id))
            component_owners: dict[str, str] = {}
            for extension in normalized:
                extension_id = extension.descriptor.extension_id
                for name, _ in extension.components:
                    previous_owner = component_owners.get(name)
                    if previous_owner is not None:
                        raise DuplicateComponentContributionError(
                            f"Component '{name}' is contributed by both "
                            f"'{previous_owner}' and '{extension_id}'."
                        )
                    component_owners[name] = extension_id

        object.__setattr__(self, "entries", normalized)
        object.__setattr__(
            self,
            "_ids",
            tuple(extension.descriptor.extension_id for extension in normalized),
        )
        object.__setattr__(
            self,
            "_component_names",
            tuple(sorted(name for extension in normalized for name, _ in extension.components)),
        )

    @property
    def ids(self) -> tuple[str, ...]:
        """Return registered extension IDs in deterministic order."""

        return self._ids

    @property
    def component_names(self) -> tuple[str, ...]:
        """Return all contributed component names in deterministic order."""

        return self._component_names

    def contains(self, extension_id: str) -> bool:
        """Return whether a component extension is registered."""

        validate_extension_id(extension_id)
        return _sorted_string_index(self._ids, extension_id) is not None

    def register(self, extension: ComponentExtension) -> "ComponentExtensionRegistry":
        """Return a new registry containing one additional component extension."""

        if not isinstance(extension, ComponentExtension):
            raise TypeError(
                "Component extension registry can register only ComponentExtension objects."
            )
        extension_id = extension.descriptor.extension_id
        if self.contains(extension_id):
            raise DuplicateExtensionRegistrationError(
                f"Component extension '{extension_id}' is already registered."
            )
        return ComponentExtensionRegistry((*self.entries, extension))

    def extension(self, extension_id: str) -> ComponentExtension:
        """Return the component extension registered under an ID."""

        validate_extension_id(extension_id)
        index = _sorted_string_index(self._ids, extension_id)
        if index is not None:
            return self.entries[index]
        raise UnknownExtensionError(f"Unknown component extension: '{extension_id}'.")

    def component_registry(self) -> ComponentRegistry:
        """Materialize all contributions as the existing ComponentRegistry."""

        values = {
            name: factory for extension in self.entries for name, factory in extension.components
        }
        return ComponentRegistry(values)


@dataclass(frozen=True, slots=True, init=False)
class RendererRegistry:
    """Immutable collection of explicitly supplied renderer extensions."""

    entries: tuple[RendererExtension, ...]
    _ids: tuple[str, ...] = field(repr=False, compare=False)

    def __init__(self, extensions: Iterable[RendererExtension] | None = None) -> None:
        if extensions is None:
            normalized: tuple[RendererExtension, ...] = ()
        else:
            collected: list[RendererExtension] = []
            seen: set[str] = set()
            for extension in extensions:
                if not isinstance(extension, RendererExtension):
                    raise TypeError("Renderer registry entries must be RendererExtension objects.")
                extension_id = extension.descriptor.extension_id
                if extension_id in seen:
                    raise DuplicateExtensionRegistrationError(
                        f"Renderer extension '{extension_id}' is already registered."
                    )
                seen.add(extension_id)
                collected.append(extension)
            normalized = tuple(sorted(collected, key=lambda item: item.descriptor.extension_id))

        object.__setattr__(self, "entries", normalized)
        object.__setattr__(
            self,
            "_ids",
            tuple(extension.descriptor.extension_id for extension in normalized),
        )

    @property
    def ids(self) -> tuple[str, ...]:
        """Return registered extension IDs in deterministic order."""

        return self._ids

    def contains(self, extension_id: str) -> bool:
        """Return whether a renderer extension is registered."""

        validate_extension_id(extension_id)
        return _sorted_string_index(self._ids, extension_id) is not None

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
        index = _sorted_string_index(self._ids, extension_id)
        if index is not None:
            return self.entries[index]
        raise UnknownExtensionError(f"Unknown renderer extension: '{extension_id}'.")

    def create(self, extension_id: str) -> Renderer:
        """Instantiate and validate the renderer registered under an ID."""

        extension = self.extension(extension_id)
        try:
            renderer = extension.factory()
        except Exception as exc:
            raise ExtensionFactoryError(
                f"Renderer extension '{extension_id}' factory failed."
            ) from exc

        if not callable(getattr(renderer, "render", None)):
            raise InvalidRendererExtensionError(
                f"Renderer extension '{extension_id}' must produce an object "
                "with a callable render() method."
            )
        return renderer


def _sorted_string_index(values: tuple[str, ...], value: str) -> int | None:
    low = 0
    high = len(values)
    while low < high:
        middle = (low + high) // 2
        candidate = values[middle]
        if candidate < value:
            low = middle + 1
        elif candidate > value:
            high = middle
        else:
            return middle
    return None


__all__ = [
    "BuildPlannerRegistry",
    "ComponentExtensionRegistry",
    "RendererRegistry",
]
