from dataclasses import dataclass
from pathlib import Path, PurePosixPath

from pypagekit import Asset, Assets, Component, Content, Page, Paragraph, Route, Site
from pypagekit.build.model import validate_build_targets
from pypagekit.components import ComponentRegistry
from pypagekit.extensions import ExtensionDescriptor, RendererExtension, RendererRegistry


@dataclass(frozen=True, slots=True)
class Label(Component):
    value: str = "ok"

    def compose(self) -> Content:
        return Paragraph(self.value)


class PlainRenderer:
    def render(self, node: object) -> str:
        return type(node).__name__


def test_build_target_validation_handles_large_sibling_set() -> None:
    targets = tuple(PurePosixPath(f"pages/{index}/index.html") for index in range(8_000))

    validate_build_targets(targets)


def test_site_lookup_handles_large_route_set_and_preserves_identity() -> None:
    routes = tuple(Route(f"/page-{index:04d}", Page(f"Page {index}")) for index in range(2_048))
    site = Site(routes)

    assert site.route("/page-2047") is routes[-1]
    assert site.has_route("/page-0000")
    assert not site.has_route("/page-9999")


def test_asset_lookup_handles_large_collection_and_preserves_identity() -> None:
    assets_tuple = tuple(
        Asset(
            Path(f"source-{index:04d}.bin"),
            PurePosixPath(f"assets/{index:04d}.bin"),
        )
        for index in range(2_048)
    )
    assets = Assets(assets_tuple)

    assert assets.asset(PurePosixPath("assets/2047.bin")) is assets_tuple[-1]
    assert assets.has_target(PurePosixPath("assets/0000.bin"))
    assert not assets.has_target(PurePosixPath("assets/9999.bin"))


def test_component_registry_handles_large_lookup_set() -> None:
    registry = ComponentRegistry({f"component-{index:04d}": Label for index in range(2_048)})

    assert registry.factory("component-2047") is Label
    assert registry.contains("component-0000")
    assert not registry.contains("component-9999")


def test_renderer_registry_handles_large_lookup_set() -> None:
    extensions = tuple(
        RendererExtension(
            ExtensionDescriptor(
                f"acme.renderer.{index:04d}",
                f"Renderer {index}",
                "1.0.0",
            ),
            PlainRenderer,
        )
        for index in range(2_048)
    )
    registry = RendererRegistry(extensions)

    assert registry.extension("acme.renderer.2047") is extensions[-1]
    assert registry.contains("acme.renderer.0000")
    assert not registry.contains("acme.renderer.9999")
