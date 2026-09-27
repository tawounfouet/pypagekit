from abc import ABC
from dataclasses import dataclass

import pytest

from pypagekit import Component, Content, Paragraph


def test_component_is_content() -> None:
    assert issubclass(Component, Content)
    assert issubclass(Component, ABC)


def test_component_cannot_be_instantiated_without_compose() -> None:
    class IncompleteComponent(Component):
        pass

    with pytest.raises(TypeError):
        IncompleteComponent()


@dataclass(frozen=True, slots=True)
class MessageComponent(Component):
    message: str

    def compose(self) -> Content:
        return Paragraph(self.message)


def test_concrete_component_can_compose_content() -> None:
    component = MessageComponent("Hello")

    assert component.compose() == Paragraph("Hello")


def test_component_has_no_render_method() -> None:
    component = MessageComponent("Hello")

    assert not hasattr(component, "render")
