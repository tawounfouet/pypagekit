from dataclasses import dataclass

import pytest

from pypagekit import Component, ComponentRef, Content, Link, Paragraph
from pypagekit.components import ComponentRegistry, ComponentRuntime
from pypagekit.exceptions import InvalidComponentNameError, UnsafeUrlError
from pypagekit.rendering import HtmlRenderer


@dataclass(frozen=True, slots=True)
class Message(Component):
    text: str

    def compose(self) -> Content:
        return Paragraph(self.text)


@dataclass(frozen=True, slots=True)
class Action(Component):
    href: str

    def compose(self) -> Content:
        return Link("Open", self.href)


def test_registered_component_text_still_uses_html_escaping() -> None:
    registry = ComponentRegistry({"message": Message})
    renderer = HtmlRenderer(component_runtime=ComponentRuntime(registry=registry))

    html = renderer.render(ComponentRef("message", {"text": "<script>alert(1)</script>"}))

    assert "<script" not in html.lower()
    assert "&lt;script&gt;" in html


def test_registered_component_action_still_uses_url_policy() -> None:
    registry = ComponentRegistry({"action": Action})
    renderer = HtmlRenderer(component_runtime=ComponentRuntime(registry=registry))

    with pytest.raises(UnsafeUrlError):
        renderer.render(ComponentRef("action", {"href": "javascript:alert(1)"}))


def test_component_registry_name_cannot_inject_markup() -> None:
    with pytest.raises(InvalidComponentNameError):
        ComponentRef('message" onclick="alert(1)')


def test_registry_has_no_global_default_instance() -> None:
    first = ComponentRegistry().register("message", Message)
    second = ComponentRegistry()

    assert first.contains("message")
    assert not second.contains("message")
