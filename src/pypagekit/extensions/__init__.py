"""Public extension contracts for PyPageKit."""

from .defaults import (
    BUILD_PLANNER_EXTENSION_ID,
    BUILTIN_COMPONENTS_EXTENSION_ID,
    HTML_RENDERER_EXTENSION_ID,
    default_build_planner_registry,
    default_component_extension_registry,
    default_renderer_registry,
)
from .discovery import (
    BUILD_PLANNER_ENTRY_POINT_GROUP,
    COMPONENT_ENTRY_POINT_GROUP,
    RENDERER_ENTRY_POINT_GROUP,
    EntryPointDiscovery,
    EntryPointReference,
    EntryPointSource,
    PluginDiscoveryResult,
)
from .lifecycle import PluginKind, PluginLifecycle, PluginState, PluginStatus
from .model import (
    PYPAGEKIT_EXTENSION_API_VERSION,
    BuildPlannerExtension,
    BuildPlannerFactory,
    ComponentExtension,
    ExtensionDescriptor,
    RendererExtension,
    RendererFactory,
    validate_extension_api_version,
    validate_extension_id,
)
from .registry import BuildPlannerRegistry, ComponentExtensionRegistry, RendererRegistry

__all__ = [
    "BUILD_PLANNER_ENTRY_POINT_GROUP",
    "BUILD_PLANNER_EXTENSION_ID",
    "BUILTIN_COMPONENTS_EXTENSION_ID",
    "COMPONENT_ENTRY_POINT_GROUP",
    "HTML_RENDERER_EXTENSION_ID",
    "PYPAGEKIT_EXTENSION_API_VERSION",
    "RENDERER_ENTRY_POINT_GROUP",
    "BuildPlannerExtension",
    "BuildPlannerFactory",
    "BuildPlannerRegistry",
    "ComponentExtension",
    "ComponentExtensionRegistry",
    "EntryPointDiscovery",
    "EntryPointReference",
    "EntryPointSource",
    "ExtensionDescriptor",
    "PluginDiscoveryResult",
    "PluginKind",
    "PluginLifecycle",
    "PluginState",
    "PluginStatus",
    "RendererExtension",
    "RendererFactory",
    "RendererRegistry",
    "default_build_planner_registry",
    "default_component_extension_registry",
    "default_renderer_registry",
    "validate_extension_api_version",
    "validate_extension_id",
]
