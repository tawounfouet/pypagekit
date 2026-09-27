from dataclasses import dataclass

from pypagekit import (
    Component,
    Container,
    Content,
    Layout,
    LayoutRegion,
    Paragraph,
)
from pypagekit.components import ComponentRuntime


@dataclass(frozen=True, slots=True)
class Message(Component):
    value: str

    def compose(self) -> Content:
        return Paragraph(self.value)


@dataclass(frozen=True, slots=True)
class AppLayout(Layout):
    message: str

    def regions(self) -> tuple[LayoutRegion, ...]:
        return (
            LayoutRegion("header", [Paragraph("Header")]),
            LayoutRegion("main", [Message(self.message)]),
        )


def test_runtime_resolves_components_inside_layout_regions() -> None:
    resolved = ComponentRuntime().resolve(AppLayout("Body"))

    assert isinstance(resolved, Container)
    main_region = resolved.children[1]

    assert isinstance(main_region, LayoutRegion)
    assert main_region.children == (Paragraph("Body"),)


def test_runtime_preserves_plain_layout_region_identity() -> None:
    region = LayoutRegion("main", [Paragraph("Body")])

    assert ComponentRuntime().resolve(region) is region


def test_runtime_recreates_region_only_when_child_component_changes() -> None:
    component = Message("Resolved")
    region = LayoutRegion("main", [component])

    resolved = ComponentRuntime().resolve(region)

    assert resolved is not region
    assert isinstance(resolved, LayoutRegion)
    assert region.children == (component,)
    assert resolved.children == (Paragraph("Resolved"),)
