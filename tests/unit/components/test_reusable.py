from dataclasses import FrozenInstanceError

import pytest

from pypagekit import (
    Attributes,
    Component,
    Container,
    Heading,
    Link,
    Paragraph,
)
from pypagekit.components import Card, Hero, Section
from pypagekit.exceptions import InvalidHeadingLevelError


def test_reusable_components_are_components() -> None:
    assert issubclass(Section, Component)
    assert issubclass(Card, Component)
    assert issubclass(Hero, Component)


def test_section_composes_heading_then_children() -> None:
    section = Section(
        "Title",
        [Paragraph("A"), Paragraph("B")],
    )

    assert section.compose() == Container(
        [
            Heading("Title", level=2),
            Paragraph("A"),
            Paragraph("B"),
        ]
    )


def test_section_preserves_outer_and_heading_attributes() -> None:
    outer = Attributes(id="section")
    heading = Attributes(classes=["title"])

    section = Section(
        "Title",
        attributes=outer,
        heading_attributes=heading,
    )

    assert section.compose() == Container(
        [
            Heading(
                "Title",
                level=2,
                attributes=heading,
            )
        ],
        attributes=outer,
    )


def test_section_normalizes_generator_children() -> None:
    section = Section(
        "Title",
        (Paragraph(str(index)) for index in range(2)),
    )

    assert section.children == (
        Paragraph("0"),
        Paragraph("1"),
    )


def test_card_without_title_composes_children_only() -> None:
    card = Card([Paragraph("Body")])

    assert card.compose() == Container([Paragraph("Body")])


def test_card_with_title_prepends_heading() -> None:
    card = Card(
        [Paragraph("Body")],
        title="Card",
    )

    assert card.compose() == Container(
        [
            Heading("Card", level=3),
            Paragraph("Body"),
        ]
    )


def test_card_empty_string_title_is_explicitly_representable() -> None:
    card = Card(title="")

    assert card.compose() == Container([Heading("", level=3)])


def test_hero_composes_title_body_and_action_in_order() -> None:
    action = Link("Start", "/start")
    hero = Hero(
        "Welcome",
        body="Intro",
        action=action,
    )

    assert hero.compose() == Container(
        [
            Heading("Welcome", level=1),
            Paragraph("Intro"),
            action,
        ]
    )


def test_hero_body_and_action_are_optional() -> None:
    assert Hero("Welcome").compose() == Container(
        [Heading("Welcome", level=1)]
    )


def test_heading_levels_are_configurable() -> None:
    assert Section("Title", heading_level=4).compose() == Container(
        [Heading("Title", level=4)]
    )
    assert Card(title="Card", heading_level=5).compose() == Container(
        [Heading("Card", level=5)]
    )
    assert Hero("Hero", heading_level=2).compose() == Container(
        [Heading("Hero", level=2)]
    )


@pytest.mark.parametrize(
    ("factory", "level"),
    [
        (lambda level: Section("Title", heading_level=level), 0),
        (lambda level: Card(title="Card", heading_level=level), 7),
        (lambda level: Hero("Hero", heading_level=level), -1),
    ],
)
def test_invalid_heading_levels_are_rejected(factory: object, level: int) -> None:
    with pytest.raises(InvalidHeadingLevelError):
        factory(level)  # type: ignore[operator]


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Section("Title", heading_level=True),
        lambda: Card(title="Card", heading_level=1.5),
        lambda: Hero("Hero", heading_level="1"),
    ],
)
def test_non_integer_heading_levels_are_rejected(factory: object) -> None:
    with pytest.raises(TypeError, match="heading level"):
        factory()  # type: ignore[operator]


def test_section_rejects_non_content_children() -> None:
    with pytest.raises(TypeError, match="only Content objects"):
        Section("Title", ["invalid"])  # type: ignore[list-item]


def test_card_rejects_non_iterable_children() -> None:
    with pytest.raises(TypeError, match="iterable of Content"):
        Card(42)  # type: ignore[arg-type]


def test_section_rejects_non_string_title() -> None:
    with pytest.raises(TypeError, match="Section title"):
        Section(42)  # type: ignore[arg-type]


def test_card_rejects_non_string_title() -> None:
    with pytest.raises(TypeError, match="Card title"):
        Card(title=42)  # type: ignore[arg-type]


def test_hero_rejects_non_string_title() -> None:
    with pytest.raises(TypeError, match="Hero title"):
        Hero(42)  # type: ignore[arg-type]


def test_hero_rejects_non_string_body() -> None:
    with pytest.raises(TypeError, match="Hero body"):
        Hero("Title", body=42)  # type: ignore[arg-type]


def test_hero_rejects_non_link_action() -> None:
    with pytest.raises(TypeError, match="Hero action"):
        Hero("Title", action=Paragraph("No"))  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "factory",
    [
        lambda: Section("Title", attributes={}),
        lambda: Card(attributes={}),
        lambda: Hero("Title", attributes={}),
    ],
)
def test_reusable_components_reject_invalid_outer_attributes(factory: object) -> None:
    with pytest.raises(TypeError, match="Attributes object"):
        factory()  # type: ignore[operator]


def test_reusable_components_are_immutable() -> None:
    section = Section("Title")

    with pytest.raises(FrozenInstanceError):
        section.title = "Changed"  # type: ignore[misc]


def test_reusable_components_do_not_define_render_method() -> None:
    assert not hasattr(Section("Title"), "render")
    assert not hasattr(Card(), "render")
    assert not hasattr(Hero("Title"), "render")
