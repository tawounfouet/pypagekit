"""Explicit installed-plugin discovery through Python entry points."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from importlib import metadata
from typing import Protocol, TypeVar, cast

from pypagekit.exceptions import (
    InvalidExtensionIdError,
    InvalidPluginEntryPointError,
    PluginDiscoveryError,
    PluginEntryPointLoadError,
    PluginProviderError,
)

from .model import (
    BuildPlannerExtension,
    ComponentExtension,
    RendererExtension,
    validate_extension_id,
)
from .registry import BuildPlannerRegistry, ComponentExtensionRegistry, RendererRegistry

BUILD_PLANNER_ENTRY_POINT_GROUP = "pypagekit.build_planners"
COMPONENT_ENTRY_POINT_GROUP = "pypagekit.components"
RENDERER_ENTRY_POINT_GROUP = "pypagekit.renderers"


class EntryPointReference(Protocol):
    """Structural subset of importlib.metadata.EntryPoint used by discovery."""

    @property
    def name(self) -> str:
        """Entry-point name."""
        ...

    @property
    def group(self) -> str:
        """Entry-point group."""
        ...

    @property
    def value(self) -> str:
        """Entry-point import target."""
        ...

    def load(self) -> object:
        """Load the entry-point target."""
        ...


EntryPointSource = Callable[[str], Iterable[EntryPointReference]]
ExtensionT = TypeVar(
    "ExtensionT",
    BuildPlannerExtension,
    ComponentExtension,
    RendererExtension,
)


@dataclass(frozen=True, slots=True)
class PluginDiscoveryResult:
    """Immutable explicit registries produced from installed entry points."""

    build_planners: BuildPlannerRegistry
    components: ComponentExtensionRegistry
    renderers: RendererRegistry

    def __post_init__(self) -> None:
        if not isinstance(self.build_planners, BuildPlannerRegistry):
            raise TypeError("Discovered build_planners must be a BuildPlannerRegistry.")
        if not isinstance(self.components, ComponentExtensionRegistry):
            raise TypeError("Discovered components must be a ComponentExtensionRegistry.")
        if not isinstance(self.renderers, RendererRegistry):
            raise TypeError("Discovered renderers must be a RendererRegistry.")


class EntryPointDiscovery:
    """Discover installed PyPageKit extension providers on explicit request."""

    def __init__(self, *, source: EntryPointSource | None = None) -> None:
        if source is not None and not callable(source):
            raise TypeError("Entry point discovery source must be callable or None.")
        self._source = source if source is not None else _installed_entry_points

    def discover(self) -> PluginDiscoveryResult:
        """Load installed extension providers into explicit immutable registries."""

        build_planners = self._discover_group(
            BUILD_PLANNER_ENTRY_POINT_GROUP,
            BuildPlannerExtension,
        )
        components = self._discover_group(
            COMPONENT_ENTRY_POINT_GROUP,
            ComponentExtension,
        )
        renderers = self._discover_group(
            RENDERER_ENTRY_POINT_GROUP,
            RendererExtension,
        )
        return PluginDiscoveryResult(
            build_planners=BuildPlannerRegistry(build_planners),
            components=ComponentExtensionRegistry(components),
            renderers=RendererRegistry(renderers),
        )

    def _discover_group(
        self,
        group: str,
        expected_type: type[ExtensionT],
    ) -> tuple[ExtensionT, ...]:
        try:
            entry_points = tuple(self._source(group))
        except Exception as exc:
            raise PluginDiscoveryError(
                f"Failed to enumerate plugin entry points for group '{group}'."
            ) from exc

        normalized = sorted(entry_points, key=lambda item: (item.name, item.value))
        contributions: list[ExtensionT] = []
        for entry_point in normalized:
            if entry_point.group != group:
                raise InvalidPluginEntryPointError(
                    f"Entry point '{entry_point.name}' belongs to group "
                    f"'{entry_point.group}', expected '{group}'."
                )

            try:
                validate_extension_id(entry_point.name)
            except InvalidExtensionIdError as exc:
                raise InvalidPluginEntryPointError(
                    f"Entry point name '{entry_point.name}' is not a valid extension ID."
                ) from exc

            try:
                provider = entry_point.load()
            except Exception as exc:
                raise PluginEntryPointLoadError(
                    f"Could not load plugin entry point '{entry_point.name}' "
                    f"from '{entry_point.value}'."
                ) from exc

            if not callable(provider):
                raise InvalidPluginEntryPointError(
                    f"Plugin entry point '{entry_point.name}' must load a callable provider."
                )

            try:
                contribution = cast(Callable[[], object], provider)()
            except Exception as exc:
                raise PluginProviderError(
                    f"Plugin provider '{entry_point.name}' failed while creating its extension."
                ) from exc

            if not isinstance(contribution, expected_type):
                raise InvalidPluginEntryPointError(
                    f"Plugin entry point '{entry_point.name}' must provide "
                    f"{expected_type.__name__}; got {type(contribution).__name__}."
                )

            if contribution.descriptor.extension_id != entry_point.name:
                raise InvalidPluginEntryPointError(
                    f"Plugin entry point '{entry_point.name}' returned extension ID "
                    f"'{contribution.descriptor.extension_id}'."
                )

            contributions.append(contribution)

        return tuple(contributions)


def _installed_entry_points(group: str) -> tuple[EntryPointReference, ...]:
    """Return installed entry points for exactly one PyPageKit plugin group."""

    return tuple(metadata.entry_points(group=group))


__all__ = [
    "BUILD_PLANNER_ENTRY_POINT_GROUP",
    "COMPONENT_ENTRY_POINT_GROUP",
    "RENDERER_ENTRY_POINT_GROUP",
    "EntryPointDiscovery",
    "EntryPointReference",
    "EntryPointSource",
    "PluginDiscoveryResult",
]
