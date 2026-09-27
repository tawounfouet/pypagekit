"""Public extension contracts for PyPageKit."""

from .defaults import HTML_RENDERER_EXTENSION_ID, default_renderer_registry
from .model import (
    ExtensionDescriptor,
    RendererExtension,
    RendererFactory,
    validate_extension_id,
)
from .registry import RendererRegistry

__all__ = [
    "HTML_RENDERER_EXTENSION_ID",
    "ExtensionDescriptor",
    "RendererExtension",
    "RendererFactory",
    "RendererRegistry",
    "default_renderer_registry",
    "validate_extension_id",
]
