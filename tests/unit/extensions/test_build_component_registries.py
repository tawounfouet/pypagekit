from dataclasses import dataclass
from pathlib import Path

import pytest

from pypagekit import Assets, Component, ComponentRef, Content, Paragraph, Site
from pypagekit.build import BuildPlan, BuildPlanner, StaticSiteGenerator
from pypagekit.components import ComponentRuntime
from pypagekit.exceptions import (
    DuplicateComponentContributionError,
    DuplicateExtensionRegistrationError,
    ExtensionFactoryError,
    InvalidBuildPlannerExtensionError,
)
from pypagekit.extensions import (
    BUILD_PLANNER_EXTENSION_ID,
    BUILTIN_COMPONENTS_EXTENSION_ID,
    BuildPlannerExtension,
    BuildPlannerRegistry,
    ComponentExtension,
    ComponentExtensionRegistry,
    ExtensionDescriptor,
    default_build_planner_registry,
    default_component_extension_registry,
)
from pypagekit.rendering import HtmlRenderer


class EmptyPlanner:
    def plan(self, site: Site, assets: Assets | None = None) -> BuildPlan:
        return BuildPlan()


class NotPlanner:
    pass


@dataclass(frozen=True, slots=True)
class Message(Component):
    text: str

    def compose(self) -> Content:
        return Paragraph(self.text)


def _build_extension(
    extension_id: str = "acme.build.empty",
    *,
    factory: object = EmptyPlanner,
) -> BuildPlannerExtension:
    return BuildPlannerExtension(
        ExtensionDescriptor(extension_id, "Empty Planner", "1.0.0"),
        factory,  # type: ignore[arg-type]
    )


def _component_extension(
    extension_id: str = "acme.components.messages",
    *,
    name: str = "message",
) -> ComponentExtension:
    return ComponentExtension(
        ExtensionDescriptor(extension_id, "Message Components", "1.0.0"),
        {name: Message},
    )


def test_build_planner_registry_is_deterministic_and_persistent() -> None:
    original = BuildPlannerRegistry((_build_extension("zeta.build"),))
    updated = original.register(_build_extension("alpha.build"))

    assert original.ids == ("zeta.build",)
    assert updated.ids == ("alpha.build", "zeta.build")


def test_build_planner_registry_rejects_duplicate_extension_ids() -> None:
    extension = _build_extension()

    with pytest.raises(DuplicateExtensionRegistrationError):
        BuildPlannerRegistry((extension, extension))


def test_build_planner_registry_validates_created_planner() -> None:
    registry = BuildPlannerRegistry((_build_extension(factory=NotPlanner),))

    with pytest.raises(InvalidBuildPlannerExtensionError, match=r"callable plan\(\)"):
        registry.create("acme.build.empty")


def test_default_build_planner_registry_exposes_builtin_planner() -> None:
    registry = default_build_planner_registry()

    assert registry.ids == (BUILD_PLANNER_EXTENSION_ID,)
    assert isinstance(registry.create(BUILD_PLANNER_EXTENSION_ID), BuildPlanner)


def test_structural_planner_can_be_injected_without_subclassing(tmp_path: Path) -> None:
    planner = BuildPlannerRegistry((_build_extension(),)).create("acme.build.empty")

    result = StaticSiteGenerator(planner=planner).generate(
        Site(),
        tmp_path / "dist",
    )

    assert result.plan == BuildPlan()


def test_component_extension_normalizes_names_deterministically() -> None:
    extension = ComponentExtension(
        ExtensionDescriptor("acme.components.ui", "UI Components", "1.0.0"),
        {"zeta": Message, "alpha": Message},
    )

    assert extension.names == ("alpha", "zeta")


def test_component_extension_registry_materializes_component_registry() -> None:
    extensions = ComponentExtensionRegistry((_component_extension(),))
    components = extensions.component_registry()

    component = components.instantiate(ComponentRef("message", {"text": "Hello"}))

    assert component == Message("Hello")


def test_component_extension_flows_through_existing_component_runtime() -> None:
    components = ComponentExtensionRegistry((_component_extension(),)).component_registry()
    renderer = HtmlRenderer(component_runtime=ComponentRuntime(registry=components))

    assert renderer.render(ComponentRef("message", {"text": "<Hello>"})) == "<p>&lt;Hello&gt;</p>"


def test_component_extension_registry_rejects_duplicate_component_names() -> None:
    with pytest.raises(DuplicateComponentContributionError, match="message"):
        ComponentExtensionRegistry(
            (
                _component_extension("alpha.components"),
                _component_extension("zeta.components"),
            )
        )


def test_component_extension_registry_register_is_persistent() -> None:
    original = ComponentExtensionRegistry()
    updated = original.register(_component_extension())

    assert original.ids == ()
    assert updated.ids == ("acme.components.messages",)
    assert updated.component_names == ("message",)


def test_default_component_extension_registry_exposes_builtin_components() -> None:
    registry = default_component_extension_registry()

    assert registry.ids == (BUILTIN_COMPONENTS_EXTENSION_ID,)
    assert registry.component_names == ("card", "hero", "section")



def test_build_planner_factory_failure_is_wrapped_with_extension_context() -> None:
    def broken_factory() -> EmptyPlanner:
        raise RuntimeError("boom")

    registry = BuildPlannerRegistry((_build_extension(factory=broken_factory),))

    with pytest.raises(ExtensionFactoryError, match=r"acme\.build\.empty") as exc_info:
        registry.create("acme.build.empty")

    assert isinstance(exc_info.value.__cause__, RuntimeError)
