from dataclasses import dataclass

from pypagekit import Attributes, Component, ComponentRef, Content, Link, Page, Paragraph
from pypagekit.components import ComponentRegistry, ComponentRuntime
from pypagekit.rendering import HtmlRenderer


@dataclass(frozen=True, slots=True)
class Notice(Component):
    text: str
    tone: str = "info"

    def compose(self) -> Content:
        return Paragraph(
            self.text,
            attributes=Attributes(data={"tone": self.tone}),
        )


@dataclass(frozen=True, slots=True)
class CallToAction(Component):
    label: str
    href: str

    def compose(self) -> Content:
        return Link(self.label, self.href)


def test_renderer_resolves_component_ref_through_runtime_registry() -> None:
    registry = ComponentRegistry({"notice": Notice})
    renderer = HtmlRenderer(component_runtime=ComponentRuntime(registry=registry))

    html = renderer.render(ComponentRef("notice", {"text": "Hello", "tone": "success"}))

    assert html == '<p data-tone="success">Hello</p>'


def test_registered_component_reference_works_inside_page() -> None:
    registry = ComponentRegistry({"notice": Notice})
    renderer = HtmlRenderer(component_runtime=ComponentRuntime(registry=registry))
    page = Page(
        title="Registry",
        content=[ComponentRef("notice", {"text": "Body"})],
    )

    assert '<p data-tone="info">Body</p>' in renderer.render(page)


def test_registry_can_hold_multiple_component_factories() -> None:
    registry = ComponentRegistry(
        {
            "notice": Notice,
            "call-to-action": CallToAction,
        }
    )
    renderer = HtmlRenderer(component_runtime=ComponentRuntime(registry=registry))

    assert renderer.render(
        ComponentRef("call-to-action", {"label": "Docs", "href": "/docs"})
    ) == '<a href="/docs">Docs</a>'
