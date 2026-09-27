from dataclasses import FrozenInstanceError

import pytest

from pypagekit import Container, Content, Heading, Paragraph, Text
from pypagekit.exceptions import InvalidContainerChildError


def test_container_is_content() -> None:
    assert issubclass(Container, Content)


def test_container_defaults_to_empty_children() -> None:
    container = Container()

    assert container.children == ()


def test_container_accepts_list_and_normalizes_to_tuple() -> None:
    heading = Heading("Title")
    paragraph = Paragraph("Body")

    container = Container([heading, paragraph])

    assert container.children == (heading, paragraph)
    assert isinstance(container.children, tuple)


def test_container_accepts_tuple() -> None:
    children = (Heading("Title"), Paragraph("Body"))

    container = Container(children)

    assert container.children == children


def test_container_accepts_generator() -> None:
    values = ["A", "B", "C"]

    container = Container(Text(value) for value in values)

    assert container.children == (Text("A"), Text("B"), Text("C"))


def test_container_preserves_child_order() -> None:
    first = Text("first")
    second = Heading("second")
    third = Paragraph("third")

    container = Container([first, second, third])

    assert container.children[0] is first
    assert container.children[1] is second
    assert container.children[2] is third


def test_container_supports_nested_containers() -> None:
    inner = Container([Paragraph("Nested")])
    outer = Container([Heading("Root"), inner])

    assert outer.children == (Heading("Root"), inner)
    assert outer.children[1] is inner


def test_container_supports_multiple_nesting_levels() -> None:
    leaf = Container([Text("leaf")])
    middle = Container([leaf])
    root = Container([middle])

    assert root.children[0] is middle
    assert middle.children[0] is leaf
    assert leaf.children == (Text("leaf"),)


def test_container_rejects_non_content_child() -> None:
    with pytest.raises(InvalidContainerChildError, match="only Content objects"):
        Container([Heading("Valid"), "invalid"])  # type: ignore[list-item]


def test_container_reports_invalid_child_type() -> None:
    with pytest.raises(InvalidContainerChildError, match="got int"):
        Container([42])  # type: ignore[list-item]


def test_container_rejects_non_iterable_children() -> None:
    with pytest.raises(TypeError, match="iterable of Content"):
        Container(42)  # type: ignore[arg-type]


def test_container_is_immutable() -> None:
    container = Container([Text("Hello")])

    with pytest.raises(FrozenInstanceError):
        container.children = ()  # type: ignore[misc]


def test_container_does_not_mutate_input_list() -> None:
    source = [Text("A")]

    container = Container(source)
    source.append(Text("B"))

    assert container.children == (Text("A"),)


def test_two_containers_with_same_children_are_equal() -> None:
    assert Container([Text("A")]) == Container([Text("A")])


def test_empty_nested_container_is_valid() -> None:
    inner = Container()
    outer = Container([inner])

    assert outer.children == (inner,)
