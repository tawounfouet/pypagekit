from dataclasses import dataclass

import pytest

from pypagekit import Assets, Component, Content, Node, Paragraph, Site
from pypagekit.build import BuildPlan
from pypagekit.exceptions import (
    InvalidExtensionDescriptorError,
    InvalidPluginLifecycleTransitionError,
    PluginActivationError,
    UnknownPluginError,
)
from pypagekit.extensions import (
    PYPAGEKIT_EXTENSION_API_VERSION,
    BuildPlannerExtension,
    BuildPlannerRegistry,
    ComponentExtension,
    ComponentExtensionRegistry,
    ExtensionDescriptor,
    PluginDiscoveryResult,
    PluginLifecycle,
    PluginState,
    RendererExtension,
    RendererRegistry,
    default_build_planner_registry,
    default_component_extension_registry,
    default_renderer_registry,
)


class PlainRenderer:
    def render(self, node: Node) -> str:
        return f"plain:{type(node).__name__}"


class InvalidRenderer:
    pass


class EmptyPlanner:
    def plan(self, site: Site, assets: Assets | None = None) -> BuildPlan:
        return BuildPlan()


class InvalidPlanner:
    pass


@dataclass(frozen=True, slots=True)
class Message(Component):
    text: str = "hello"

    def compose(self) -> Content:
        return Paragraph(self.text)


def _descriptor(
    extension_id: str,
    *,
    api_version: str | None = PYPAGEKIT_EXTENSION_API_VERSION,
) -> ExtensionDescriptor:
    return ExtensionDescriptor(
        extension_id,
        extension_id,
        "1.0.0",
        api_version=api_version,
    )


def _renderer(
    extension_id: str = "acme.renderer.plain",
    *,
    api_version: str | None = PYPAGEKIT_EXTENSION_API_VERSION,
    factory: object = PlainRenderer,
) -> RendererExtension:
    return RendererExtension(
        _descriptor(extension_id, api_version=api_version),
        factory,  # type: ignore[arg-type]
    )


def _planner(
    extension_id: str = "acme.build.empty",
    *,
    api_version: str | None = PYPAGEKIT_EXTENSION_API_VERSION,
    factory: object = EmptyPlanner,
) -> BuildPlannerExtension:
    return BuildPlannerExtension(
        _descriptor(extension_id, api_version=api_version),
        factory,  # type: ignore[arg-type]
    )


def _components(
    extension_id: str = "acme.components.message",
    *,
    api_version: str | None = PYPAGEKIT_EXTENSION_API_VERSION,
) -> ComponentExtension:
    return ComponentExtension(
        _descriptor(extension_id, api_version=api_version),
        {"message": Message},
    )


def _discovery(
    *,
    planners: tuple[BuildPlannerExtension, ...] = (),
    components: tuple[ComponentExtension, ...] = (),
    renderers: tuple[RendererExtension, ...] = (),
) -> PluginDiscoveryResult:
    return PluginDiscoveryResult(
        BuildPlannerRegistry(planners),
        ComponentExtensionRegistry(components),
        RendererRegistry(renderers),
    )


def test_extension_api_version_requires_major_minor_form() -> None:
    descriptor = _descriptor("acme.renderer.compatible")

    assert descriptor.api_version == PYPAGEKIT_EXTENSION_API_VERSION

    with pytest.raises(InvalidExtensionDescriptorError, match=r"major.*minor"):
        _descriptor("acme.renderer.invalid", api_version="0.7.0")


def test_builtin_extensions_declare_current_api_version() -> None:
    assert default_build_planner_registry().entries[0].descriptor.api_version == (
        PYPAGEKIT_EXTENSION_API_VERSION
    )
    assert default_component_extension_registry().entries[0].descriptor.api_version == (
        PYPAGEKIT_EXTENSION_API_VERSION
    )
    assert default_renderer_registry().entries[0].descriptor.api_version == (
        PYPAGEKIT_EXTENSION_API_VERSION
    )


def test_from_discovery_is_deterministic_and_does_not_qualify() -> None:
    lifecycle = PluginLifecycle.from_discovery(
        _discovery(
            planners=(_planner("zeta.build"),),
            components=(_components("beta.components"),),
            renderers=(_renderer("alpha.renderer"),),
        )
    )

    assert lifecycle.ids == (
        "alpha.renderer",
        "beta.components",
        "zeta.build",
    )
    assert tuple(status.state for status in lifecycle.statuses) == (
        PluginState.DISCOVERED,
        PluginState.DISCOVERED,
        PluginState.DISCOVERED,
    )
    assert lifecycle.active_plugins.renderers.ids == ()


def test_qualify_accepts_conformant_extensions() -> None:
    discovered = PluginLifecycle.from_discovery(
        _discovery(
            planners=(_planner(),),
            components=(_components(),),
            renderers=(_renderer(),),
        )
    )

    qualified = discovered.qualify()

    assert all(status.state is PluginState.QUALIFIED for status in qualified.statuses)
    assert qualified.is_conformant
    assert qualified.qualified_plugins.build_planners.ids == ("acme.build.empty",)
    assert qualified.qualified_plugins.components.ids == ("acme.components.message",)
    assert qualified.qualified_plugins.renderers.ids == ("acme.renderer.plain",)
    assert all(status.state is PluginState.DISCOVERED for status in discovered.statuses)


def test_missing_api_version_is_rejected() -> None:
    lifecycle = PluginLifecycle.from_discovery(
        _discovery(renderers=(_renderer(api_version=None),))
    ).qualify()

    status = lifecycle.status("acme.renderer.plain")

    assert status.state is PluginState.REJECTED
    assert "does not declare" in (status.reason or "")
    assert lifecycle.rejected_ids == ("acme.renderer.plain",)
    assert not lifecycle.is_conformant
    assert lifecycle.qualified_plugins.renderers.ids == ()


def test_incompatible_api_version_is_rejected() -> None:
    lifecycle = PluginLifecycle.from_discovery(
        _discovery(renderers=(_renderer(api_version="0.8"),))
    ).qualify()

    status = lifecycle.status("acme.renderer.plain")

    assert status.state is PluginState.REJECTED
    assert "incompatible" in (status.reason or "")


def test_invalid_renderer_factory_result_is_rejected() -> None:
    lifecycle = PluginLifecycle.from_discovery(
        _discovery(renderers=(_renderer(factory=InvalidRenderer),))
    ).qualify()

    status = lifecycle.status("acme.renderer.plain")

    assert status.state is PluginState.REJECTED
    assert "InvalidRendererExtensionError" in (status.reason or "")


def test_invalid_build_planner_factory_result_is_rejected() -> None:
    lifecycle = PluginLifecycle.from_discovery(
        _discovery(planners=(_planner(factory=InvalidPlanner),))
    ).qualify()

    status = lifecycle.status("acme.build.empty")

    assert status.state is PluginState.REJECTED
    assert "InvalidBuildPlannerExtensionError" in (status.reason or "")


def test_factory_exception_becomes_rejected_conformance() -> None:
    def broken_renderer() -> PlainRenderer:
        raise RuntimeError("boom")

    lifecycle = PluginLifecycle.from_discovery(
        _discovery(renderers=(_renderer(factory=broken_renderer),))
    ).qualify()

    status = lifecycle.status("acme.renderer.plain")

    assert status.state is PluginState.REJECTED
    assert status.reason == "renderer conformance failed with RuntimeError"


def test_global_extension_id_collision_is_rejected_across_kinds() -> None:
    extension_id = "acme.shared.plugin"
    lifecycle = PluginLifecycle.from_discovery(
        _discovery(
            planners=(_planner(extension_id),),
            renderers=(_renderer(extension_id),),
        )
    ).qualify()

    assert tuple(status.state for status in lifecycle.statuses) == (
        PluginState.REJECTED,
        PluginState.REJECTED,
    )
    assert all("duplicated" in (status.reason or "") for status in lifecycle.statuses)

    with pytest.raises(PluginActivationError, match="ambiguous"):
        lifecycle.status(extension_id)


def test_activation_requires_qualification_first() -> None:
    lifecycle = PluginLifecycle.from_discovery(_discovery(renderers=(_renderer(),)))

    with pytest.raises(InvalidPluginLifecycleTransitionError, match="qualification first"):
        lifecycle.activate()


def test_activate_all_qualified_plugins() -> None:
    qualified = PluginLifecycle.from_discovery(
        _discovery(
            planners=(_planner(),),
            components=(_components(),),
            renderers=(_renderer(),),
        )
    ).qualify()

    active = qualified.activate()

    assert active.active_ids == (
        "acme.build.empty",
        "acme.components.message",
        "acme.renderer.plain",
    )
    assert all(status.state is PluginState.ACTIVE for status in active.statuses)
    assert active.active_plugins.build_planners.ids == ("acme.build.empty",)
    assert active.active_plugins.components.component_names == ("message",)
    assert active.active_plugins.renderers.ids == ("acme.renderer.plain",)
    assert qualified.active_ids == ()


def test_activate_subset_preserves_other_qualified_plugins() -> None:
    qualified = PluginLifecycle.from_discovery(
        _discovery(
            planners=(_planner(),),
            renderers=(_renderer(),),
        )
    ).qualify()

    active = qualified.activate(("acme.renderer.plain",))

    assert active.status("acme.renderer.plain").state is PluginState.ACTIVE
    assert active.status("acme.build.empty").state is PluginState.QUALIFIED
    assert active.active_plugins.renderers.ids == ("acme.renderer.plain",)
    assert active.active_plugins.build_planners.ids == ()


def test_rejected_plugin_cannot_be_activated() -> None:
    qualified = PluginLifecycle.from_discovery(
        _discovery(renderers=(_renderer(api_version="0.8"),))
    ).qualify()

    with pytest.raises(PluginActivationError, match="rejected"):
        qualified.activate(("acme.renderer.plain",))


def test_unknown_plugin_cannot_be_activated() -> None:
    qualified = PluginLifecycle.from_discovery(_discovery(renderers=(_renderer(),))).qualify()

    with pytest.raises(UnknownPluginError, match="missing"):
        qualified.activate(("acme.renderer.missing",))


def test_duplicate_activation_request_is_rejected() -> None:
    qualified = PluginLifecycle.from_discovery(_discovery(renderers=(_renderer(),))).qualify()

    with pytest.raises(PluginActivationError, match="more than once"):
        qualified.activate(("acme.renderer.plain", "acme.renderer.plain"))


def test_deactivate_returns_plugin_to_qualified_state() -> None:
    active = (
        PluginLifecycle.from_discovery(_discovery(renderers=(_renderer(),))).qualify().activate()
    )

    deactivated = active.deactivate(("acme.renderer.plain",))

    assert deactivated.status("acme.renderer.plain").state is PluginState.QUALIFIED
    assert deactivated.active_plugins.renderers.ids == ()
    assert active.status("acme.renderer.plain").state is PluginState.ACTIVE


def test_deactivate_all_active_plugins() -> None:
    active = (
        PluginLifecycle.from_discovery(
            _discovery(
                planners=(_planner(),),
                renderers=(_renderer(),),
            )
        )
        .qualify()
        .activate()
    )

    deactivated = active.deactivate()

    assert deactivated.active_ids == ()
    assert all(status.state is PluginState.QUALIFIED for status in deactivated.statuses)


def test_deactivating_inactive_plugin_fails_explicitly() -> None:
    qualified = PluginLifecycle.from_discovery(_discovery(renderers=(_renderer(),))).qualify()

    with pytest.raises(PluginActivationError, match="not active"):
        qualified.deactivate(("acme.renderer.plain",))


def test_active_renderer_is_usable_through_existing_registry_contract() -> None:
    active = (
        PluginLifecycle.from_discovery(_discovery(renderers=(_renderer(),))).qualify().activate()
    )

    renderer = active.active_plugins.renderers.create("acme.renderer.plain")

    assert renderer.render(Paragraph("hello")) == "plain:Paragraph"


def test_active_planner_is_usable_through_existing_registry_contract() -> None:
    active = PluginLifecycle.from_discovery(_discovery(planners=(_planner(),))).qualify().activate()

    planner = active.active_plugins.build_planners.create("acme.build.empty")

    assert planner.plan(Site()) == BuildPlan()
