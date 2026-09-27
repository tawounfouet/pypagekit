"""Built-in extension registrations."""

from pypagekit import __version__
from pypagekit.rendering import HtmlRenderer

from .model import ExtensionDescriptor, RendererExtension
from .registry import RendererRegistry

HTML_RENDERER_EXTENSION_ID = "pypagekit.renderer.html"


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
    "HTML_RENDERER_EXTENSION_ID",
    "default_renderer_registry",
]
