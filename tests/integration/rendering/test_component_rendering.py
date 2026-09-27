from dataclasses import dataclass

import pytest

from pypagekit import (
    Attributes,
    Component,
    Container,
    Content,
    Heading,
    Link,
    Page,
    Paragraph,
)
from pypagekit.components import ComponentRuntime
from pypagekit.exceptions import ComponentResolutionDepthError, UnsafeUrlError
from pypagekit.rendering import HtmlRenderer


@dataclass(frozen=True, slots=True)
class Hero(Component):
    title: str
    body: str

    def compose(self) -> Content:
        return Container(
            [
                Heading(
                    self.title,
                    attributes=Attributes(classes=["hero-title"]),
                ),
                Paragraph(self.body),
            ],
            attributes=Attributes(id="hero", classes=["hero"]),
        )


@dataclass(frozen=True, slots=True)
class Wrapper(Component):
    content: Content

    def compose(self) -> Content:
        return Container([self.content])


@dataclass(frozen=True, slots=True)
class UnsafeLinkComponent(Component):
    def compose(self) -> Content:
        return Link("Unsafe", "javascript:alert(1)")


class FreshRecursiveComponent(Component):
    def compose(self) -> Content:
        return FreshRecursiveComponent()


def test_renderer_renders_component_as_resolved_content() -> None:
    html = HtmlRenderer().render(Hero("Welcome", "Hello"))

    assert html == (
        '<div class="hero" id="hero"><h1 class="hero-title">Welcome</h1>'
        "<p>Hello</p></div>"
    )


def test_renderer_resolves_nested_components() -> None:
    component = Wrapper(Wrapper(Paragraph("Nested")))

    assert HtmlRenderer().render(component) == "<div><div><p>Nested</p></div></div>"


def test_component_can_live_directly_inside_page_content() -> None:
    page = Page(
        title="Components",
        content=[Hero("Welcome", "Hello")],
    )

    html = HtmlRenderer().render(page)

    assert '<div class="hero" id="hero">' in html
    assert '<h1 class="hero-title">Welcome</h1>' in html


def test_component_output_still_uses_text_escaping() -> None:
    html = HtmlRenderer().render(Hero("<Welcome>", "A & B"))

    assert "&lt;Welcome&gt;" in html
    assert "<p>A &amp; B</p>" in html


def test_component_output_still_uses_url_security_policy() -> None:
    with pytest.raises(UnsafeUrlError):
        HtmlRenderer().render(UnsafeLinkComponent())


def test_renderer_accepts_custom_component_runtime() -> None:
    renderer = HtmlRenderer(
        component_runtime=ComponentRuntime(max_depth=2),
    )

    with pytest.raises(ComponentResolutionDepthError, match="max_depth=2"):
        renderer.render(FreshRecursiveComponent())
