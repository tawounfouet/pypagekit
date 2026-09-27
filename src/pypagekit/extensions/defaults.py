"""Built-in extension registrations."""

from pypagekit import __version__
from pypagekit.build import BuildPlanner
from pypagekit.components import Card, Hero, Section
from pypagekit.rendering import HtmlRenderer

from .model import (
    BuildPlannerExtension,
    ComponentExtension,
    ExtensionDescriptor,
    RendererExtension,
)
from .registry import BuildPlannerRegistry, ComponentExtensionRegistry, RendererRegistry

BUILD_PLANNER_EXTENSION_ID = "pypagekit.build.planner"
BUILTIN_COMPONENTS_EXTENSION_ID = "pypagekit.components.builtin"
HTML_RENDERER_EXTENSION_ID = "pypagekit.renderer.html"


def default_build_planner_registry() -> BuildPlannerRegistry:
    """Return the explicit registry containing the built-in build planner."""

    return BuildPlannerRegistry(
        (
            BuildPlannerExtension(
                descriptor=ExtensionDescriptor(
                    extension_id=BUILD_PLANNER_EXTENSION_ID,
                    name="Static Build Planner",
                    version=__version__,
                ),
                factory=BuildPlanner,
            ),
        )
    )


def default_component_extension_registry() -> ComponentExtensionRegistry:
    """Return built-in reusable components as an explicit extension bundle."""

    return ComponentExtensionRegistry(
        (
            ComponentExtension(
                descriptor=ExtensionDescriptor(
                    extension_id=BUILTIN_COMPONENTS_EXTENSION_ID,
                    name="Built-in Components",
                    version=__version__,
                ),
                components={
                    "card": Card,
                    "hero": Hero,
                    "section": Section,
                },
            ),
        )
    )


def default_renderer_registry() -> RendererRegistry:
    """Return the explicit registry containing built-in renderer extensions."""

    return RendererRegistry(
        (
            RendererExtension(
                descriptor=ExtensionDescriptor(
                    extension_id=HTML_RENDERER_EXTENSION_ID,
                    name="HTML Renderer",
                    version=__version__,
                ),
                factory=HtmlRenderer,
            ),
        )
    )


__all__ = [
    "BUILD_PLANNER_EXTENSION_ID",
    "BUILTIN_COMPONENTS_EXTENSION_ID",
    "HTML_RENDERER_EXTENSION_ID",
    "default_build_planner_registry",
    "default_component_extension_registry",
    "default_renderer_registry",
]
