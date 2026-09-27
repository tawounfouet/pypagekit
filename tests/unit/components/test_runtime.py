from dataclasses import dataclass

import pytest

from pypagekit import Attributes, Component, Container, Content, Heading, Paragraph, Text
from pypagekit.components import ComponentRuntime
from pypagekit.exceptions import (
    ComponentCycleError,
    ComponentResolutionDepthError,
    InvalidComponentResultError,
)


@dataclass(frozen=True, slots=True)
class MessageComponent(Component):
    message: str

    def compose(self) -> Content:
        return Paragraph(self.message)


@dataclass(frozen=True, slots=True)
class NestedComponent(Component):
    message: str

    def compose(self) -> Content:
        return MessageComponent(self.message)


@dataclass(frozen=True, slots=True)
class SectionComponent(Component):
    title: str
    body: str

    def compose(self) -> Content:
        return Container(
            [
                Heading(self.title),
                MessageComponent(self.body),
            ],
            attributes=Attributes(classes=["section"]),
        )


class InvalidComponent(Component):
    def compose(self) -> Content:
        return "not-content"  # type: ignore[return-value]


class SelfCycleComponent(Component):
    def compose(self) -> Content:
        return self


class ReferenceComponent(Component):
    def __init__(self) -> None:
        self.target: Content | None = None

    def compose(self) -> Content:
        assert self.target is not None
        return self.target


class FreshRecursiveComponent(Component):
    def compose(self) -> Content:
        return FreshRecursiveComponent()


def test_runtime_resolves_simple_component() -> None:
    resolved = ComponentRuntime().resolve(MessageComponent("Hello"))

    assert resolved == Paragraph("Hello")


def test_runtime_resolves_component_returning_component() -> None:
    resolved = ComponentRuntime().resolve(NestedComponent("Hello"))

    assert resolved == Paragraph("Hello")


def test_runtime_resolves_components_nested_inside_container() -> None:
    component = SectionComponent("Title", "Body")

    resolved = ComponentRuntime().resolve(component)

    assert resolved == Container(
        [
            Heading("Title"),
            Paragraph("Body"),
        ],
        attributes=Attributes(classes=["section"]),
    )


def test_runtime_preserves_unmodified_plain_content_identity() -> None:
    paragraph = Paragraph("Hello")

    assert ComponentRuntime().resolve(paragraph) is paragraph


def test_runtime_preserves_container_identity_when_no_component_exists() -> None:
    container = Container([Text("A"), Paragraph("B")])

    assert ComponentRuntime().resolve(container) is container


def test_runtime_does_not_mutate_source_container() -> None:
    component = MessageComponent("Resolved")
    source = Container([component])

    resolved = ComponentRuntime().resolve(source)

    assert source.children == (component,)
    assert resolved == Container([Paragraph("Resolved")])
    assert resolved is not source


def test_invalid_component_result_is_rejected() -> None:
    with pytest.raises(InvalidComponentResultError, match="must return Content"):
        ComponentRuntime().resolve(InvalidComponent())


def test_direct_component_cycle_is_rejected() -> None:
    with pytest.raises(ComponentCycleError, match="SelfCycleComponent"):
        ComponentRuntime().resolve(SelfCycleComponent())


def test_indirect_component_cycle_is_rejected() -> None:
    first = ReferenceComponent()
    second = ReferenceComponent()
    first.target = second
    second.target = first

    with pytest.raises(ComponentCycleError, match="ReferenceComponent"):
        ComponentRuntime().resolve(first)


def test_fresh_recursive_components_hit_depth_guard() -> None:
    runtime = ComponentRuntime(max_depth=3)

    with pytest.raises(ComponentResolutionDepthError, match="max_depth=3"):
        runtime.resolve(FreshRecursiveComponent())


@pytest.mark.parametrize("max_depth", [0, -1])
def test_runtime_rejects_non_positive_max_depth(max_depth: int) -> None:
    with pytest.raises(ValueError, match="at least 1"):
        ComponentRuntime(max_depth=max_depth)


@pytest.mark.parametrize("max_depth", [True, 1.5, "10"])
def test_runtime_rejects_non_integer_max_depth(max_depth: object) -> None:
    with pytest.raises(TypeError, match="must be an integer"):
        ComponentRuntime(max_depth=max_depth)  # type: ignore[arg-type]


def test_runtime_rejects_non_content_input() -> None:
    with pytest.raises(TypeError, match="only Content"):
        ComponentRuntime().resolve("invalid")  # type: ignore[arg-type]
