from dataclasses import FrozenInstanceError

import pytest

from pypagekit import Content, Node, Page
from pypagekit.exceptions import (
    InvalidPageContentError,
    InvalidPageLanguageError,
    InvalidPageTitleError,
)


class ExampleContent(Content):
    pass


def test_page_is_a_node() -> None:
    assert issubclass(Page, Node)


def test_page_normalizes_title_and_language() -> None:
    page = Page("  Home  ", lang="  fr  ")

    assert page.title == "Home"
    assert page.lang == "fr"


def test_page_uses_english_as_default_language() -> None:
    assert Page("Home").lang == "en"


def test_page_accepts_an_iterable_and_stores_an_immutable_tuple() -> None:
    first = ExampleContent()
    second = ExampleContent()

    page = Page("Home", [first, second])

    assert page.content == (first, second)
    assert isinstance(page.content, tuple)


def test_page_preserves_content_order() -> None:
    first = ExampleContent()
    second = ExampleContent()

    page = Page("Home", (first, second))

    assert page.content[0] is first
    assert page.content[1] is second


def test_page_preserves_optional_description() -> None:
    page = Page("Home", description="A small page")

    assert page.description == "A small page"


@pytest.mark.parametrize("title", ["", " ", "\n\t"])
def test_page_rejects_empty_title_after_normalization(title: str) -> None:
    with pytest.raises(InvalidPageTitleError):
        Page(title)


@pytest.mark.parametrize("lang", ["", " ", "\n\t"])
def test_page_rejects_empty_language_after_normalization(lang: str) -> None:
    with pytest.raises(InvalidPageLanguageError):
        Page("Home", lang=lang)


def test_page_rejects_non_content_children() -> None:
    with pytest.raises(InvalidPageContentError, match="only Content objects"):
        Page("Home", [ExampleContent(), "not-content"])  # type: ignore[list-item]


def test_page_rejects_non_iterable_content() -> None:
    with pytest.raises(TypeError, match="iterable of Content"):
        Page("Home", 42)  # type: ignore[arg-type]


def test_page_rejects_non_string_title() -> None:
    with pytest.raises(TypeError, match="title must be a string"):
        Page(42)  # type: ignore[arg-type]


def test_page_rejects_non_string_language() -> None:
    with pytest.raises(TypeError, match="language must be a string"):
        Page("Home", lang=42)  # type: ignore[arg-type]


def test_page_rejects_non_string_description() -> None:
    with pytest.raises(TypeError, match="description must be a string or None"):
        Page("Home", description=42)  # type: ignore[arg-type]


def test_page_is_immutable() -> None:
    page = Page("Home")

    with pytest.raises(FrozenInstanceError):
        page.title = "Changed"  # type: ignore[misc]
