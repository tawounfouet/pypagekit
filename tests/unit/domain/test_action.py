from dataclasses import FrozenInstanceError

import pytest

from pypagekit import Content, Link
from pypagekit.domain import Action
from pypagekit.exceptions import InvalidLinkHrefError


def test_action_is_content() -> None:
    assert issubclass(Action, Content)


def test_link_is_an_action() -> None:
    assert issubclass(Link, Action)


def test_link_preserves_label_and_href_exactly() -> None:
    link = Link(label="  About & more  ", href=" /about?from=home ")

    assert link.label == "  About & more  "
    assert link.href == " /about?from=home "


@pytest.mark.parametrize(
    "href",
    [
        "/about",
        "#intro",
        "https://example.com/docs",
        "mailto:hello@example.com",
    ],
)
def test_link_accepts_common_destination_forms(href: str) -> None:
    assert Link(label="Destination", href=href).href == href


def test_link_accepts_empty_label() -> None:
    assert Link(label="", href="/").label == ""


@pytest.mark.parametrize("href", ["", " ", "\n\t"])
def test_link_rejects_empty_href_after_whitespace_check(href: str) -> None:
    with pytest.raises(InvalidLinkHrefError, match="must not be empty"):
        Link(label="Broken", href=href)


def test_link_rejects_non_string_label() -> None:
    with pytest.raises(TypeError, match="Link label must be a string"):
        Link(label=42, href="/")  # type: ignore[arg-type]


def test_link_rejects_non_string_href() -> None:
    with pytest.raises(TypeError, match="Link href must be a string"):
        Link(label="Home", href=42)  # type: ignore[arg-type]


def test_link_is_immutable() -> None:
    link = Link(label="Home", href="/")

    with pytest.raises(FrozenInstanceError):
        link.href = "/changed"  # type: ignore[misc]
