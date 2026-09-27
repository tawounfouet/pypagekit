from dataclasses import dataclass

import pytest

from pypagekit import Component, ComponentRef, Container, Content, Paragraph
from pypagekit.components import ComponentRegistry, ComponentRuntime
from pypagekit.exceptions import MissingComponentRegistryError


@dataclass(frozen=True, slots=True)
class Message(Component):
    text: str

    def compose(self) -> Content:
        return Paragraph(self.text)


def test_runtime_resolves_registered_component_reference() -> None:
    registry = ComponentRegistry({"message": Message})
    runtime = ComponentRuntime(registry=registry)

    assert runtime.resolve(ComponentRef("message", {"text": "Hello"})) == Paragraph("Hello")


def test_runtime_resolves_component_ref_nested_in_container() -> None:
    registry = ComponentRegistry({"message": Message})
    container = Container([ComponentRef("message", {"text": "Hello"})])

    assert ComponentRuntime(registry=registry).resolve(container) == Container(
        [Paragraph("Hello")]
    )


def test_runtime_requires_registry_for_component_ref() -> None:
    with pytest.raises(MissingComponentRegistryError, match="message"):
        ComponentRuntime().resolve(ComponentRef("message", {"text": "Hello"}))


def test_runtime_registry_is_explicitly_exposed() -> None:
    registry = ComponentRegistry({"message": Message})

    assert ComponentRuntime(registry=registry).registry is registry


def test_runtime_rejects_invalid_registry_type() -> None:
    with pytest.raises(TypeError, match="ComponentRegistry or None"):
        ComponentRuntime(registry={})  # type: ignore[arg-type]
