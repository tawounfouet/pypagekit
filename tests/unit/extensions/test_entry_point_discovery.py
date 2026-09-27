from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest

from pypagekit import Assets, Component, Content, Node, Paragraph, Site
from pypagekit.build import BuildPlan
from pypagekit.exceptions import (
    DuplicateComponentContributionError,
    InvalidPluginEntryPointError,
    PluginDiscoveryError,
    PluginEntryPointLoadError,
    PluginProviderError,
)
from pypagekit.extensions import (
    BUILD_PLANNER_ENTRY_POINT_GROUP,
    COMPONENT_ENTRY_POINT_GROUP,
    RENDERER_ENTRY_POINT_GROUP,
    BuildPlannerExtension,
    ComponentExtension,
    EntryPointDiscovery,
    ExtensionDescriptor,
    RendererExtension,
)


class PlainRenderer:
    def render(self, node: Node) -> str:
        return f"plain:{type(node).__name__}"


class EmptyPlanner:
    def plan(self, site: Site, assets: Assets | None = None) -> BuildPlan:
        return BuildPlan()


@dataclass(frozen=True, slots=True)
class Message(Component):
    text: str = "hello"

    def compose(self) -> Content:
        return Paragraph(self.text)


@dataclass
class FakeEntryPoint:
    name: str
    group: str
    value: str
    target: object = None
    load_error: Exception | None = None
    loaded: bool = False

    def load(self) -> object:
        self.loaded = True
        if self.load_error is not None:
            raise self.load_error
        return self.target


def _build_extension(extension_id: str = "acme.build.empty") -> BuildPlannerExtension:
    return BuildPlannerExtension(
        ExtensionDescriptor(extension_id, "Empty Planner", "1.0.0"),
        EmptyPlanner,
    )


def _component_extension(
    extension_id: str = "acme.components.message",
    *,
    name: str = "message",
) -> ComponentExtension:
    return ComponentExtension(
        ExtensionDescriptor(extension_id, "Message Components", "1.0.0"),
        {name: Message},
    )


def _renderer_extension(extension_id: str = "acme.renderer.plain") -> RendererExtension:
    return RendererExtension(
        ExtensionDescriptor(extension_id, "Plain Renderer", "1.0.0"),
        PlainRenderer,
    )


def _source(
    values: dict[str, tuple[FakeEntryPoint, ...]],
    calls: list[str] | None = None,
) -> Callable[[str], tuple[FakeEntryPoint, ...]]:
    def select(group: str) -> tuple[FakeEntryPoint, ...]:
        if calls is not None:
            calls.append(group)
        return values.get(group, ())

    return select


def test_discovery_constructor_performs_no_enumeration_or_loading() -> None:
    calls: list[str] = []
    entry_point = FakeEntryPoint(
        "acme.renderer.plain",
        RENDERER_ENTRY_POINT_GROUP,
        "acme:renderer",
        _renderer_extension,
    )

    EntryPointDiscovery(source=_source({RENDERER_ENTRY_POINT_GROUP: (entry_point,)}, calls))

    assert calls == []
    assert not entry_point.loaded


def test_discovery_feeds_explicit_registries() -> None:
    calls: list[str] = []
    discovery = EntryPointDiscovery(
        source=_source(
            {
                BUILD_PLANNER_ENTRY_POINT_GROUP: (
                    FakeEntryPoint(
                        "acme.build.empty",
                        BUILD_PLANNER_ENTRY_POINT_GROUP,
                        "acme:build",
                        _build_extension,
                    ),
                ),
                COMPONENT_ENTRY_POINT_GROUP: (
                    FakeEntryPoint(
                        "acme.components.message",
                        COMPONENT_ENTRY_POINT_GROUP,
                        "acme:components",
                        _component_extension,
                    ),
                ),
                RENDERER_ENTRY_POINT_GROUP: (
                    FakeEntryPoint(
                        "acme.renderer.plain",
                        RENDERER_ENTRY_POINT_GROUP,
                        "acme:renderer",
                        _renderer_extension,
                    ),
                ),
            },
            calls,
        )
    )

    result = discovery.discover()

    assert calls == [
        BUILD_PLANNER_ENTRY_POINT_GROUP,
        COMPONENT_ENTRY_POINT_GROUP,
        RENDERER_ENTRY_POINT_GROUP,
    ]
    assert result.build_planners.ids == ("acme.build.empty",)
    assert result.components.ids == ("acme.components.message",)
    assert result.components.component_names == ("message",)
    assert result.renderers.ids == ("acme.renderer.plain",)


def test_discovery_sorts_entry_points_deterministically() -> None:
    discovery = EntryPointDiscovery(
        source=_source(
            {
                RENDERER_ENTRY_POINT_GROUP: (
                    FakeEntryPoint(
                        "zeta.renderer.plain",
                        RENDERER_ENTRY_POINT_GROUP,
                        "zeta:provider",
                        lambda: _renderer_extension("zeta.renderer.plain"),
                    ),
                    FakeEntryPoint(
                        "alpha.renderer.plain",
                        RENDERER_ENTRY_POINT_GROUP,
                        "alpha:provider",
                        lambda: _renderer_extension("alpha.renderer.plain"),
                    ),
                )
            }
        )
    )

    assert discovery.discover().renderers.ids == (
        "alpha.renderer.plain",
        "zeta.renderer.plain",
    )


def test_duplicate_entry_point_names_fail_before_loading() -> None:
    first = FakeEntryPoint(
        "acme.renderer.plain",
        RENDERER_ENTRY_POINT_GROUP,
        "alpha:provider",
        _renderer_extension,
    )
    second = FakeEntryPoint(
        "acme.renderer.plain",
        RENDERER_ENTRY_POINT_GROUP,
        "zeta:provider",
        _renderer_extension,
    )

    with pytest.raises(InvalidPluginEntryPointError, match="Duplicate plugin entry point"):
        EntryPointDiscovery(
            source=_source({RENDERER_ENTRY_POINT_GROUP: (first, second)})
        ).discover()

    assert not first.loaded
    assert not second.loaded


def test_invalid_entry_point_name_fails_before_loading() -> None:
    entry_point = FakeEntryPoint(
        "ACME renderer",
        RENDERER_ENTRY_POINT_GROUP,
        "acme:provider",
        _renderer_extension,
    )

    with pytest.raises(InvalidPluginEntryPointError, match="valid extension ID"):
        EntryPointDiscovery(source=_source({RENDERER_ENTRY_POINT_GROUP: (entry_point,)})).discover()

    assert not entry_point.loaded


def test_wrong_group_from_source_is_rejected_before_loading() -> None:
    entry_point = FakeEntryPoint(
        "acme.renderer.plain",
        "wrong.group",
        "acme:provider",
        _renderer_extension,
    )

    with pytest.raises(InvalidPluginEntryPointError, match="expected"):
        EntryPointDiscovery(source=_source({RENDERER_ENTRY_POINT_GROUP: (entry_point,)})).discover()

    assert not entry_point.loaded


def test_non_callable_entry_point_target_is_rejected() -> None:
    entry_point = FakeEntryPoint(
        "acme.renderer.plain",
        RENDERER_ENTRY_POINT_GROUP,
        "acme:value",
        object(),
    )

    with pytest.raises(InvalidPluginEntryPointError, match="callable provider"):
        EntryPointDiscovery(source=_source({RENDERER_ENTRY_POINT_GROUP: (entry_point,)})).discover()


def test_entry_point_load_failure_is_wrapped() -> None:
    entry_point = FakeEntryPoint(
        "acme.renderer.plain",
        RENDERER_ENTRY_POINT_GROUP,
        "missing.module:provider",
        load_error=ImportError("boom"),
    )

    with pytest.raises(PluginEntryPointLoadError) as exc_info:
        EntryPointDiscovery(source=_source({RENDERER_ENTRY_POINT_GROUP: (entry_point,)})).discover()

    assert isinstance(exc_info.value.__cause__, ImportError)


def test_provider_failure_is_wrapped() -> None:
    def broken_provider() -> RendererExtension:
        raise RuntimeError("provider failed")

    entry_point = FakeEntryPoint(
        "acme.renderer.plain",
        RENDERER_ENTRY_POINT_GROUP,
        "acme:broken",
        broken_provider,
    )

    with pytest.raises(PluginProviderError) as exc_info:
        EntryPointDiscovery(source=_source({RENDERER_ENTRY_POINT_GROUP: (entry_point,)})).discover()

    assert isinstance(exc_info.value.__cause__, RuntimeError)


def test_provider_must_return_expected_extension_type() -> None:
    entry_point = FakeEntryPoint(
        "acme.renderer.plain",
        RENDERER_ENTRY_POINT_GROUP,
        "acme:wrong",
        _build_extension,
    )

    with pytest.raises(InvalidPluginEntryPointError, match="RendererExtension"):
        EntryPointDiscovery(source=_source({RENDERER_ENTRY_POINT_GROUP: (entry_point,)})).discover()


def test_entry_point_name_must_match_returned_extension_id() -> None:
    entry_point = FakeEntryPoint(
        "acme.renderer.public",
        RENDERER_ENTRY_POINT_GROUP,
        "acme:renderer",
        _renderer_extension,
    )

    with pytest.raises(InvalidPluginEntryPointError, match="returned extension ID"):
        EntryPointDiscovery(source=_source({RENDERER_ENTRY_POINT_GROUP: (entry_point,)})).discover()


def test_component_collisions_across_plugins_remain_explicit() -> None:
    first = FakeEntryPoint(
        "alpha.components.message",
        COMPONENT_ENTRY_POINT_GROUP,
        "alpha:components",
        lambda: _component_extension("alpha.components.message"),
    )
    second = FakeEntryPoint(
        "zeta.components.message",
        COMPONENT_ENTRY_POINT_GROUP,
        "zeta:components",
        lambda: _component_extension("zeta.components.message"),
    )

    with pytest.raises(DuplicateComponentContributionError, match="message"):
        EntryPointDiscovery(
            source=_source({COMPONENT_ENTRY_POINT_GROUP: (first, second)})
        ).discover()


def test_entry_point_source_failure_is_wrapped() -> None:
    def broken_source(group: str) -> tuple[FakeEntryPoint, ...]:
        raise OSError(group)

    with pytest.raises(PluginDiscoveryError) as exc_info:
        EntryPointDiscovery(source=broken_source).discover()

    assert isinstance(exc_info.value.__cause__, OSError)


def test_discovered_planner_is_usable_by_existing_generator(tmp_path: Path) -> None:
    discovery = EntryPointDiscovery(
        source=_source(
            {
                BUILD_PLANNER_ENTRY_POINT_GROUP: (
                    FakeEntryPoint(
                        "acme.build.empty",
                        BUILD_PLANNER_ENTRY_POINT_GROUP,
                        "acme:build",
                        _build_extension,
                    ),
                )
            }
        )
    )

    planner = discovery.discover().build_planners.create("acme.build.empty")

    assert planner.plan(Site()) == BuildPlan()
    assert tmp_path.exists()
