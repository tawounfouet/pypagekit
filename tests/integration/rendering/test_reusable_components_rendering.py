from dataclasses import dataclass

from pypagekit import (
    Attributes,
    Component,
    Content,
    Layout,
    LayoutRegion,
    Link,
    Page,
    Paragraph,
)
from pypagekit.components import Card, Hero, Section
from pypagekit.rendering import HtmlRenderer


@dataclass(frozen=True, slots=True)
class Badge(Component):
    label: str

    def compose(self) -> Content:
        return Paragraph(self.label)


@dataclass(frozen=True, slots=True)
class PageLayout(Layout):
    content: Content

    def regions(self) -> tuple[LayoutRegion, ...]:
        return (LayoutRegion("main", [self.content]),)


def test_section_renders_through_existing_renderer_pipeline() -> None:
    section = Section(
        "Overview",
        [Paragraph("Body")],
        attributes=Attributes(id="overview"),
        heading_attributes=Attributes(classes=["section-title"]),
    )

    assert HtmlRenderer().render(section) == (
        '<div id="overview"><h2 class="section-title">Overview</h2><p>Body</p></div>'
    )


def test_card_has_no_implicit_css_class_or_marker() -> None:
    html = HtmlRenderer().render(
        Card(
            [Paragraph("Body")],
            title="Card",
        )
    )

    assert html == "<div><h3>Card</h3><p>Body</p></div>"
    assert 'class="' not in html
    assert "data-component" not in html


def test_hero_renders_existing_primitives_only() -> None:
    hero = Hero(
        "Welcome",
        body="Intro",
        action=Link("Start", "/start"),
    )

    assert HtmlRenderer().render(hero) == (
        '<div><h1>Welcome</h1><p>Intro</p><a href="/start">Start</a></div>'
    )


def test_reusable_component_can_contain_custom_component() -> None:
    card = Card(
        [Badge("New")],
        title="Status",
    )

    assert HtmlRenderer().render(card) == ("<div><h3>Status</h3><p>New</p></div>")


def test_reusable_components_can_be_nested() -> None:
    content = Section(
        "Page",
        [
            Card(
                [Paragraph("Body")],
                title="Card",
            )
        ],
    )

    assert HtmlRenderer().render(content) == (
        "<div><h2>Page</h2><div><h3>Card</h3><p>Body</p></div></div>"
    )


def test_reusable_component_can_live_inside_layout_region() -> None:
    layout = PageLayout(
        Hero(
            "Welcome",
            body="Body",
        )
    )

    html = HtmlRenderer().render(layout)

    assert 'data-layout-region="main"' in html
    assert "<h1>Welcome</h1>" in html
    assert "<p>Body</p>" in html


def test_reusable_component_can_live_directly_inside_page() -> None:
    page = Page(
        title="Reusable",
        content=[
            Section(
                "Content",
                [Paragraph("Body")],
            )
        ],
    )

    html = HtmlRenderer().render(page)

    assert "<h2>Content</h2>" in html
    assert "<p>Body</p>" in html
