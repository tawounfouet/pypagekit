from dataclasses import dataclass

from pypagekit import (
    Attributes,
    Component,
    Content,
    Heading,
    Layout,
    LayoutRegion,
    Page,
    Paragraph,
)
from pypagekit.rendering import HtmlRenderer


@dataclass(frozen=True, slots=True)
class Notice(Component):
    message: str

    def compose(self) -> Content:
        return Paragraph(self.message)


@dataclass(frozen=True, slots=True)
class DashboardLayout(Layout):
    def regions(self) -> tuple[LayoutRegion, ...]:
        return (
            LayoutRegion(
                "header",
                [Heading("Dashboard")],
                attributes=Attributes(classes=["top"]),
            ),
            LayoutRegion(
                "main",
                [Notice("Content")],
                attributes=Attributes(id="content"),
            ),
            LayoutRegion("footer", [Paragraph("Footer")]),
        )


def test_layout_renders_regions_in_declared_order() -> None:
    html = HtmlRenderer().render(DashboardLayout())

    assert html == (
        '<div><div class="top" data-layout-region="header"><h1>Dashboard</h1></div>'
        '<div data-layout-region="main" id="content"><p>Content</p></div>'
        '<div data-layout-region="footer"><p>Footer</p></div></div>'
    )


def test_layout_can_be_used_directly_inside_page() -> None:
    page = Page(
        title="Dashboard",
        content=[DashboardLayout()],
    )

    html = HtmlRenderer().render(page)

    assert '<div data-layout-region="header">' in html
    assert 'data-layout-region="main"' in html
    assert 'data-layout-region="footer"' in html


def test_layout_region_does_not_add_css_classes_implicitly() -> None:
    html = HtmlRenderer().render(LayoutRegion("main", [Paragraph("Body")]))

    assert html == '<div data-layout-region="main"><p>Body</p></div>'
    assert 'class="' not in html


def test_intrinsic_region_marker_overrides_conflicting_data_hook() -> None:
    region = LayoutRegion(
        "main",
        attributes=Attributes(data={"layout-region": "spoofed"}),
    )

    html = HtmlRenderer().render(region)

    assert html == '<div data-layout-region="main"></div>'
