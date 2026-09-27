from dataclasses import FrozenInstanceError

import pytest

from pypagekit import (
    Navigation,
    NavigationItem,
    Page,
    Route,
    Site,
    Sitemap,
    SitemapEntry,
)
from pypagekit.exceptions import (
    DuplicateSiteRouteError,
    InvalidSiteNavigationError,
    InvalidSiteRouteError,
    NavigationRouteMismatchError,
    UnknownNavigationRouteError,
    UnknownSiteRouteError,
)


def route(path: str, title: str | None = None) -> Route:
    return Route(path, Page(title or path))


def test_site_can_be_empty() -> None:
    site = Site()

    assert site.routes == ()
    assert site.pages == ()
    assert site.paths == ()
    assert site.navigation is None
    assert site.sitemap == Sitemap()


def test_site_preserves_route_declaration_order() -> None:
    home = route("/", "Home")
    about = route("/about", "About")
    docs = route("/docs", "Docs")

    site = Site([home, about, docs])

    assert site.routes == (home, about, docs)
    assert site.paths == ("/", "/about", "/docs")
    assert site.pages == (home.page, about.page, docs.page)


def test_site_accepts_route_generator() -> None:
    site = Site(route(f"/page-{index}") for index in range(2))

    assert site.paths == ("/page-0", "/page-1")


def test_site_rejects_duplicate_canonical_route_paths() -> None:
    first = route("/about", "First")
    second = route("/about/", "Second")

    with pytest.raises(DuplicateSiteRouteError, match="/about"):
        Site([first, second])


def test_site_rejects_non_route_child() -> None:
    with pytest.raises(InvalidSiteRouteError, match="Route objects"):
        Site([Page("Not a route")])  # type: ignore[list-item]


def test_site_rejects_non_iterable_routes() -> None:
    with pytest.raises(TypeError, match="iterable of Route"):
        Site(42)  # type: ignore[arg-type]


def test_site_rejects_invalid_navigation_type() -> None:
    with pytest.raises(InvalidSiteNavigationError, match="Navigation"):
        Site([], navigation="invalid")  # type: ignore[arg-type]


def test_navigation_can_reference_subset_of_site_routes() -> None:
    home = route("/", "Home")
    docs = route("/docs", "Docs")
    hidden = route("/hidden", "Hidden")
    navigation = Navigation(
        [
            NavigationItem("Home", home),
            NavigationItem("Docs", docs),
        ]
    )

    site = Site([home, docs, hidden], navigation=navigation)

    assert site.navigation is navigation
    assert site.sitemap.paths == ("/", "/docs", "/hidden")


def test_navigation_route_must_belong_to_site() -> None:
    home = route("/", "Home")
    external = route("/external", "External")
    navigation = Navigation([NavigationItem("External", external)])

    with pytest.raises(UnknownNavigationRouteError, match="/external"):
        Site([home], navigation=navigation)


def test_navigation_must_reference_canonical_site_route_object() -> None:
    canonical = route("/about", "About")
    duplicate_object = route("/about", "About")
    navigation = Navigation([NavigationItem("About", duplicate_object)])

    with pytest.raises(NavigationRouteMismatchError, match="/about"):
        Site([canonical], navigation=navigation)


def test_route_lookup_returns_canonical_site_object() -> None:
    about = route("/about", "About")
    site = Site([about])

    assert site.route("/about") is about
    assert site.route("/about/") is about
    assert site.has_route("/about")
    assert site.has_route("/about/")


def test_unknown_route_lookup_fails_explicitly() -> None:
    site = Site([route("/", "Home")])

    with pytest.raises(UnknownSiteRouteError, match="/missing"):
        site.route("/missing")


def test_has_route_returns_false_for_valid_unknown_path() -> None:
    site = Site([route("/", "Home")])

    assert not site.has_route("/missing")


def test_site_is_immutable() -> None:
    site = Site([route("/", "Home")])

    with pytest.raises(FrozenInstanceError):
        site.navigation = Navigation()  # type: ignore[misc]


def test_sitemap_preserves_all_routes_in_order() -> None:
    home = route("/", "Home")
    about = route("/about", "About")

    sitemap = Sitemap([home, about])

    assert sitemap.routes == (home, about)
    assert sitemap.paths == ("/", "/about")
    assert sitemap.entries == (
        SitemapEntry(home),
        SitemapEntry(about),
    )


def test_sitemap_entry_exposes_route_path_and_page() -> None:
    about = route("/about", "About")
    entry = SitemapEntry(about)

    assert entry.route is about
    assert entry.path == "/about"
    assert entry.page is about.page


def test_sitemap_rejects_duplicate_paths() -> None:
    with pytest.raises(DuplicateSiteRouteError, match="/docs"):
        Sitemap(
            [
                route("/docs", "Docs A"),
                route("/docs/", "Docs B"),
            ]
        )


def test_sitemap_rejects_invalid_route() -> None:
    with pytest.raises(InvalidSiteRouteError):
        Sitemap([Page("Invalid")])  # type: ignore[list-item]


def test_sitemap_entry_rejects_invalid_route() -> None:
    with pytest.raises(InvalidSiteRouteError):
        SitemapEntry(Page("Invalid"))  # type: ignore[arg-type]
