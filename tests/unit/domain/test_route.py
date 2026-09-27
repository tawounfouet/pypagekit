from dataclasses import FrozenInstanceError

import pytest

from pypagekit import Page, Paragraph, Route
from pypagekit.domain import normalize_route_path
from pypagekit.exceptions import InvalidRoutePageError, InvalidRoutePathError


def make_page() -> Page:
    return Page("Route", [Paragraph("Body")])


def test_route_associates_canonical_path_with_page() -> None:
    page = make_page()
    route = Route("/about", page)

    assert route.path == "/about"
    assert route.page is page


def test_root_route_is_preserved() -> None:
    route = Route("/", make_page())

    assert route.path == "/"
    assert route.is_root
    assert route.segments == ()


def test_non_root_trailing_slash_is_canonicalized() -> None:
    route = Route("/docs/", make_page())

    assert route.path == "/docs"
    assert route.segments == ("docs",)


def test_nested_route_exposes_ordered_segments() -> None:
    route = Route("/docs/getting-started", make_page())

    assert not route.is_root
    assert route.segments == ("docs", "getting-started")


def test_route_preserves_unicode_and_valid_percent_encoding() -> None:
    assert Route("/café", make_page()).path == "/café"
    assert Route("/caf%C3%A9", make_page()).path == "/caf%C3%A9"


def test_route_is_immutable() -> None:
    route = Route("/about", make_page())

    with pytest.raises(FrozenInstanceError):
        route.path = "/changed"  # type: ignore[misc]


@pytest.mark.parametrize(
    "path",
    [
        "",
        "about",
        "docs/getting-started",
        "//example.com/path",
        "/docs//api",
        "/docs/./api",
        "/docs/../api",
        "/docs/%2e/api",
        "/docs/%2E%2E/api",
        "/docs/%2f/api",
        "/docs/%2Fapi",
        "/docs/%5c/api",
        "/docs/%00/api",
        "/docs\\api",
        "/docs?lang=en",
        "/docs?",
        "/docs#intro",
        "/docs#",
        "https://example.com/docs",
        "http://example.com/docs",
        "mailto:docs@example.com",
        "/bad%escape",
        "/bad%2",
        "/bad%GG",
    ],
)
def test_route_rejects_invalid_or_ambiguous_paths(path: str) -> None:
    with pytest.raises(InvalidRoutePathError):
        Route(path, make_page())


def test_route_rejects_raw_control_characters() -> None:
    with pytest.raises(InvalidRoutePathError, match="control"):
        Route("/docs\x00api", make_page())


def test_route_path_must_be_string() -> None:
    with pytest.raises(TypeError, match="must be a string"):
        Route(42, make_page())  # type: ignore[arg-type]


def test_route_target_must_be_page() -> None:
    with pytest.raises(InvalidRoutePageError, match="Page"):
        Route("/about", Paragraph("Not a page"))  # type: ignore[arg-type]


def test_normalize_route_path_is_deterministic() -> None:
    assert normalize_route_path("/docs/") == "/docs"
    assert normalize_route_path("/docs") == "/docs"
