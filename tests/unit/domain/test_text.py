from dataclasses import FrozenInstanceError

import pytest

from pypagekit import Content, Heading, Paragraph, Text
from pypagekit.exceptions import InvalidHeadingLevelError


def test_text_is_content() -> None:
    assert issubclass(Text, Content)


def test_text_preserves_value_exactly() -> None:
    value = "  A & B < C  "

    assert Text(value).value == value


def test_text_accepts_empty_string() -> None:
    assert Text("").value == ""


def test_text_rejects_non_string_value() -> None:
    with pytest.raises(TypeError, match="Text value must be a string"):
        Text(42)  # type: ignore[arg-type]


def test_text_is_immutable() -> None:
    node = Text("hello")

    with pytest.raises(FrozenInstanceError):
        node.value = "changed"  # type: ignore[misc]


def test_heading_is_content() -> None:
    assert issubclass(Heading, Content)


def test_heading_defaults_to_level_one() -> None:
    heading = Heading("Hello")

    assert heading.text == "Hello"
    assert heading.level == 1


@pytest.mark.parametrize("level", [1, 2, 3, 4, 5, 6])
def test_heading_accepts_supported_levels(level: int) -> None:
    assert Heading("Title", level=level).level == level


@pytest.mark.parametrize("level", [0, 7, -1, 100])
def test_heading_rejects_levels_outside_supported_range(level: int) -> None:
    with pytest.raises(InvalidHeadingLevelError, match="between 1 and 6"):
        Heading("Title", level=level)


@pytest.mark.parametrize("level", [True, False, 1.5, "2", None])
def test_heading_rejects_non_integer_levels(level: object) -> None:
    with pytest.raises(TypeError, match="Heading level must be an integer"):
        Heading("Title", level=level)  # type: ignore[arg-type]


def test_heading_preserves_text_exactly() -> None:
    text = "  Heading & <raw>  "

    assert Heading(text).text == text


def test_heading_accepts_empty_text() -> None:
    assert Heading("").text == ""


def test_heading_rejects_non_string_text() -> None:
    with pytest.raises(TypeError, match="Heading text must be a string"):
        Heading(42)  # type: ignore[arg-type]


def test_heading_is_immutable() -> None:
    heading = Heading("Hello")

    with pytest.raises(FrozenInstanceError):
        heading.level = 2  # type: ignore[misc]


def test_paragraph_is_content() -> None:
    assert issubclass(Paragraph, Content)


def test_paragraph_preserves_text_exactly() -> None:
    text = "  Paragraph & <raw>  "

    assert Paragraph(text).text == text


def test_paragraph_accepts_empty_text() -> None:
    assert Paragraph("").text == ""


def test_paragraph_accepts_unicode() -> None:
    text = "Café — 東京 — 你好 — 🔥"

    assert Paragraph(text).text == text


def test_paragraph_rejects_non_string_text() -> None:
    with pytest.raises(TypeError, match="Paragraph text must be a string"):
        Paragraph(42)  # type: ignore[arg-type]


def test_paragraph_is_immutable() -> None:
    paragraph = Paragraph("Hello")

    with pytest.raises(FrozenInstanceError):
        paragraph.text = "changed"  # type: ignore[misc]
