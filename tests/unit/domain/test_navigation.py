from dataclasses import FrozenInstanceError

import pytest

from pypagekit import Navigation, NavigationItem, Page, Route
from pypagekit.exceptions import (
    DuplicateNavigationRouteError,
    InvalidNavigationChildError,
    InvalidNavigationLabelError,
    InvalidNavigationRouteError,
    NavigationCycleError,
)


def route(path: str, title: str | None = None) -> Route:
    return Route(path, Page(title or path))


def test_navigation_item_references_route_and_preserves_label() -> None:
    target = route("/about", "About")
    item = NavigationItem("About us", target)

    assert item.label == "About us"
    assert item.route is target
    assert item.children == ()


def test_navigation_item_normalizes_children_to_tuple() -> None:
    child = NavigationItem("API", route("/docs/api"))
    item = NavigationItem("Docs", route("/docs"), [child])

    assert item.children == (child,)


def test_navigation_item_accepts_generator_children() -> None:
    item = NavigationItem(
        "Docs",
        route("/docs"),
        (NavigationItem(str(index), route(f"/docs/{index}")) for index in range(2)),
    )

    assert tuple(child.label for child in item.children) == ("0", "1")


@pytest.mark.parametrize("label", ["", " ", "\t", "\n"])
def test_navigation_item_rejects_empty_labels(label: str) -> None:
    with pytest.raises(InvalidNavigationLabelError):
        NavigationItem(label, route("/about"))


def test_navigation_item_rejects_non_string_label() -> None:
    with pytest.raises(TypeError, match="label must be a string"):
        NavigationItem(42, route("/about"))  # type: ignore[arg-type]


def test_navigation_item_rejects_non_route_target() -> None:
    with pytest.raises(InvalidNavigationRouteError, match="Route"):
        NavigationItem("About", Page("About"))  # type: ignore[arg-type]


def test_navigation_item_rejects_invalid_child() -> None:
    with pytest.raises(InvalidNavigationChildError, match="NavigationItem"):
        NavigationItem("Docs", route("/docs"), ["invalid"])  # type: ignore[list-item]


def test_navigation_item_is_immutable() -> None:
    item = NavigationItem("About", route("/about"))

    with pytest.raises(FrozenInstanceError):
        item.label = "Changed"  # type: ignore[misc]


def test_navigation_can_be_empty() -> None:
    navigation = Navigation()

    assert navigation.items == ()
    assert navigation.walk() == ()
    assert navigation.routes == ()
    assert navigation.route_paths == ()


def test_navigation_preserves_depth_first_declaration_order() -> None:
    api = NavigationItem("API", route("/docs/api"))
    guide = NavigationItem("Guide", route("/docs/guide"))
    docs = NavigationItem("Docs", route("/docs"), [api, guide])
    about = NavigationItem("About", route("/about"))

    navigation = Navigation([docs, about])

    assert navigation.walk() == (docs, api, guide, about)
    assert navigation.route_paths == (
        "/docs",
        "/docs/api",
        "/docs/guide",
        "/about",
    )


def test_navigation_rejects_duplicate_route_path_at_top_level() -> None:
    first = NavigationItem("First", route("/about", "First"))
    second = NavigationItem("Second", route("/about", "Second"))

    with pytest.raises(DuplicateNavigationRouteError, match="/about"):
        Navigation([first, second])


def test_navigation_rejects_duplicate_route_path_nested() -> None:
    child = NavigationItem("Nested", route("/about", "Nested"))
    parent = NavigationItem("Parent", route("/docs"), [child])
    duplicate = NavigationItem("Duplicate", route("/about", "Duplicate"))

    with pytest.raises(DuplicateNavigationRouteError, match="/about"):
        Navigation([parent, duplicate])


def test_navigation_allows_duplicate_labels_for_distinct_routes() -> None:
    navigation = Navigation(
        [
            NavigationItem("Docs", route("/docs")),
            NavigationItem("Docs", route("/reference")),
        ]
    )

    assert navigation.route_paths == ("/docs", "/reference")


def test_navigation_rejects_object_cycle() -> None:
    item = NavigationItem("Loop", route("/loop"))
    object.__setattr__(item, "children", (item,))

    with pytest.raises(NavigationCycleError, match="/loop"):
        Navigation([item])


def test_navigation_rejects_invalid_top_level_item() -> None:
    with pytest.raises(InvalidNavigationChildError, match="NavigationItem"):
        Navigation(["invalid"])  # type: ignore[list-item]


def test_navigation_rejects_non_iterable_items() -> None:
    with pytest.raises(TypeError, match="iterable of NavigationItem"):
        Navigation(42)  # type: ignore[arg-type]
