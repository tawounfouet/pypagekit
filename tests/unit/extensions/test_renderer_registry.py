from dataclasses import FrozenInstanceError

import pytest

from pypagekit import Node, Text
from pypagekit.exceptions import (
    DuplicateExtensionRegistrationError,
    InvalidExtensionDescriptorError,
    InvalidExtensionIdError,
    InvalidRendererExtensionError,
    UnknownExtensionError,
)
from pypagekit.extensions import (
    HTML_RENDERER_EXTENSION_ID,
    ExtensionDescriptor,
    RendererExtension,
    RendererRegistry,
    default_renderer_registry,
)


class PlainRenderer:
    def render(self, node: Node) -> str:
        return f"plain:{type(node).__name__}"


class NotRenderer:
    pass


def _extension(
    extension_id: str = "acme.renderer.plain",
    *,
    factory: object = PlainRenderer,
) -> RendererExtension:
    return RendererExtension(
        ExtensionDescriptor(extension_id, "Plain Renderer", "1.0.0"),
        factory,  # type: ignore[arg-type]
    )


def test_extension_descriptor_is_immutable() -> None:
    descriptor = ExtensionDescriptor("acme.renderer.plain", "Plain Renderer", "1.0.0")

    with pytest.raises(FrozenInstanceError):
        descriptor.name = "Other"  # type: ignore[misc]


@pytest.mark.parametrize(
    "extension_id",
    [
        "",
        "Acme.renderer",
        ".acme",
        "acme.",
        "acme..renderer",
        "acme_renderer",
        "acme/renderer",
        " acme.renderer",
    ],
)
def test_extension_descriptor_rejects_invalid_ids(extension_id: str) -> None:
    with pytest.raises(InvalidExtensionIdError):
        ExtensionDescriptor(extension_id, "Renderer", "1.0.0")


@pytest.mark.parametrize(("name", "version"), [("", "1.0"), (" Renderer", "1.0"), ("R", "")])
def test_extension_descriptor_rejects_invalid_literals(name: str, version: str) -> None:
    with pytest.raises(InvalidExtensionDescriptorError):
        ExtensionDescriptor("acme.renderer.test", name, version)


def test_registry_ids_are_deterministic() -> None:
    registry = RendererRegistry(
        (
            _extension("zeta.renderer.text"),
            _extension("alpha.renderer.text"),
        )
    )

    assert registry.ids == ("alpha.renderer.text", "zeta.renderer.text")


def test_register_is_persistent_not_mutating() -> None:
    base = RendererRegistry()
    extended = base.register(_extension())

    assert base.ids == ()
    assert extended.ids == ("acme.renderer.plain",)


def test_registry_rejects_duplicate_ids() -> None:
    extension = _extension()

    with pytest.raises(DuplicateExtensionRegistrationError):
        RendererRegistry((extension, extension))


def test_unknown_extension_fails_explicitly() -> None:
    with pytest.raises(UnknownExtensionError, match="acme.renderer.missing"):
        RendererRegistry().extension("acme.renderer.missing")


def test_registry_creates_renderer() -> None:
    renderer = RendererRegistry((_extension(),)).create("acme.renderer.plain")

    assert renderer.render(Text("hello")) == "plain:Text"


def test_registry_rejects_invalid_factory_result() -> None:
    registry = RendererRegistry((_extension(factory=NotRenderer),))

    with pytest.raises(InvalidRendererExtensionError, match="callable render"):
        registry.create("acme.renderer.plain")


def test_default_registry_exposes_html_renderer() -> None:
    registry = default_renderer_registry()

    assert registry.ids == (HTML_RENDERER_EXTENSION_ID,)
    assert registry.create(HTML_RENDERER_EXTENSION_ID).render(Text("<b>")) == "&lt;b&gt;"
