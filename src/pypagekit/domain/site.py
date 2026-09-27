"""Site aggregate and sitemap projection for logical routes."""

from collections.abc import Iterable
from dataclasses import dataclass

from pypagekit.exceptions import (
    DuplicateSiteRouteError,
    InvalidSiteNavigationError,
    InvalidSiteRouteError,
    NavigationRouteMismatchError,
    UnknownNavigationRouteError,
    UnknownSiteRouteError,
)

from .navigation import Navigation
from .page import Page
from .route import Route, normalize_route_path


@dataclass(frozen=True, slots=True)
class SitemapEntry:
    """Immutable sitemap entry backed by one canonical site route."""

    route: Route

    def __post_init__(self) -> None:
        if not isinstance(self.route, Route):
            raise InvalidSiteRouteError("Sitemap entry route must be a Route object.")

    @property
    def path(self) -> str:
        """Canonical logical path represented by this entry."""

        return self.route.path

    @property
    def page(self) -> Page:
        """Page associated with this sitemap entry."""

        return self.route.page


@dataclass(frozen=True, slots=True, init=False)
class Sitemap:
    """Immutable ordered sitemap projection over canonical routes."""

    entries: tuple[SitemapEntry, ...]

    def __init__(self, routes: Iterable[Route] = ()) -> None:
        normalized_routes = _normalize_site_routes(routes, owner="Sitemap")
        object.__setattr__(
            self,
            "entries",
            tuple(SitemapEntry(route) for route in normalized_routes),
        )

    @property
    def routes(self) -> tuple[Route, ...]:
        """Return sitemap routes in declaration order."""

        return tuple(entry.route for entry in self.entries)

    @property
    def paths(self) -> tuple[str, ...]:
        """Return canonical sitemap paths in declaration order."""

        return tuple(entry.path for entry in self.entries)


@dataclass(frozen=True, slots=True, init=False)
class Site:
    """Immutable aggregate owning routes, navigation, and sitemap projection."""

    routes: tuple[Route, ...]
    navigation: Navigation | None
    sitemap: Sitemap

    def __init__(
        self,
        routes: Iterable[Route] = (),
        *,
        navigation: Navigation | None = None,
    ) -> None:
        normalized_routes = _normalize_site_routes(routes, owner="Site")

        if navigation is not None and not isinstance(navigation, Navigation):
            raise InvalidSiteNavigationError(
                "Site navigation must be a Navigation object or None."
            )

        _validate_navigation_membership(normalized_routes, navigation)

        object.__setattr__(self, "routes", normalized_routes)
        object.__setattr__(self, "navigation", navigation)
        object.__setattr__(self, "sitemap", Sitemap(normalized_routes))

    @property
    def paths(self) -> tuple[str, ...]:
        """Return canonical site paths in declaration order."""

        return tuple(route.path for route in self.routes)

    @property
    def pages(self) -> tuple[Page, ...]:
        """Return site pages in route declaration order."""

        return tuple(route.page for route in self.routes)

    def has_route(self, path: str) -> bool:
        """Return whether a canonicalized logical path belongs to this site."""

        normalized_path = normalize_route_path(path)
        return any(route.path == normalized_path for route in self.routes)

    def route(self, path: str) -> Route:
        """Look up a site route by logical path."""

        normalized_path = normalize_route_path(path)
        for route in self.routes:
            if route.path == normalized_path:
                return route

        raise UnknownSiteRouteError(
            f"Route '{normalized_path}' does not belong to this site."
        )


def _normalize_site_routes(
    routes: Iterable[Route],
    *,
    owner: str,
) -> tuple[Route, ...]:
    try:
        normalized_routes = tuple(routes)
    except TypeError as exc:
        raise TypeError(f"{owner} routes must be an iterable of Route objects.") from exc

    invalid_routes = [
        route for route in normalized_routes if not isinstance(route, Route)
    ]
    if invalid_routes:
        invalid_type = type(invalid_routes[0]).__name__
        raise InvalidSiteRouteError(
            f"{owner} routes must contain only Route objects; got {invalid_type}."
        )

    seen_paths: set[str] = set()
    for route in normalized_routes:
        if route.path in seen_paths:
            raise DuplicateSiteRouteError(
                f"Route '{route.path}' appears more than once in {owner.lower()}."
            )
        seen_paths.add(route.path)

    return normalized_routes


def _validate_navigation_membership(
    routes: tuple[Route, ...],
    navigation: Navigation | None,
) -> None:
    if navigation is None:
        return

    routes_by_path = {route.path: route for route in routes}
    for navigation_route in navigation.routes:
        site_route = routes_by_path.get(navigation_route.path)
        if site_route is None:
            raise UnknownNavigationRouteError(
                f"Navigation route '{navigation_route.path}' does not belong to this site."
            )
        if site_route is not navigation_route:
            raise NavigationRouteMismatchError(
                f"Navigation route '{navigation_route.path}' must reference "
                "the canonical Route object owned by Site."
            )
