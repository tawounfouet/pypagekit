"""Hierarchical navigation models built from logical routes."""

from collections.abc import Iterable
from dataclasses import dataclass

from pypagekit.exceptions import (
    DuplicateNavigationRouteError,
    InvalidNavigationChildError,
    InvalidNavigationLabelError,
    InvalidNavigationRouteError,
    NavigationCycleError,
)

from .route import Route


@dataclass(frozen=True, slots=True, init=False)
class NavigationItem:
    """Immutable labeled reference to a route with ordered child items."""

    label: str
    route: Route
    children: tuple["NavigationItem", ...]

    def __init__(
        self,
        label: str,
        route: Route,
        children: Iterable["NavigationItem"] = (),
    ) -> None:
        if not isinstance(label, str):
            raise TypeError("Navigation item label must be a string.")
        if not label.strip():
            raise InvalidNavigationLabelError(
                "Navigation item label must not be empty."
            )
        if not isinstance(route, Route):
            raise InvalidNavigationRouteError(
                "Navigation item route must be a Route object."
            )

        try:
            normalized_children = tuple(children)
        except TypeError as exc:
            raise TypeError(
                "Navigation item children must be an iterable of NavigationItem objects."
            ) from exc

        invalid_children = [
            child
            for child in normalized_children
            if not isinstance(child, NavigationItem)
        ]
        if invalid_children:
            invalid_type = type(invalid_children[0]).__name__
            raise InvalidNavigationChildError(
                "Navigation item children must contain only NavigationItem objects; "
                f"got {invalid_type}."
            )

        object.__setattr__(self, "label", label)
        object.__setattr__(self, "route", route)
        object.__setattr__(self, "children", normalized_children)


@dataclass(frozen=True, slots=True, init=False)
class Navigation:
    """Immutable validated navigation tree."""

    items: tuple[NavigationItem, ...]

    def __init__(self, items: Iterable[NavigationItem] = ()) -> None:
        try:
            normalized_items = tuple(items)
        except TypeError as exc:
            raise TypeError(
                "Navigation items must be an iterable of NavigationItem objects."
            ) from exc

        invalid_items = [
            item for item in normalized_items if not isinstance(item, NavigationItem)
        ]
        if invalid_items:
            invalid_type = type(invalid_items[0]).__name__
            raise InvalidNavigationChildError(
                "Navigation must contain only NavigationItem objects; "
                f"got {invalid_type}."
            )

        _validate_navigation_tree(normalized_items)
        object.__setattr__(self, "items", normalized_items)

    @property
    def routes(self) -> tuple[Route, ...]:
        """Return every referenced route in depth-first declaration order."""

        return tuple(item.route for item in self.walk())

    @property
    def route_paths(self) -> tuple[str, ...]:
        """Return every referenced canonical route path in tree order."""

        return tuple(route.path for route in self.routes)

    def walk(self) -> tuple[NavigationItem, ...]:
        """Return all navigation items in depth-first declaration order."""

        result: list[NavigationItem] = []

        def visit(item: NavigationItem) -> None:
            result.append(item)
            for child in item.children:
                visit(child)

        for item in self.items:
            visit(item)

        return tuple(result)


def _validate_navigation_tree(items: tuple[NavigationItem, ...]) -> None:
    seen_paths: set[str] = set()
    active_ids: set[int] = set()

    def visit(item: NavigationItem) -> None:
        identity = id(item)
        if identity in active_ids:
            raise NavigationCycleError(
                f"Navigation cycle detected at route '{item.route.path}'."
            )

        if item.route.path in seen_paths:
            raise DuplicateNavigationRouteError(
                f"Route '{item.route.path}' appears more than once in navigation."
            )

        active_ids.add(identity)
        seen_paths.add(item.route.path)
        try:
            for child in item.children:
                visit(child)
        finally:
            active_ids.remove(identity)

    for item in items:
        visit(item)
