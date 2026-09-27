import pytest

from pypagekit import Navigation, NavigationItem, Page, Route, Site
from pypagekit.exceptions import InvalidRoutePathError


def test_site_lookup_inherits_route_path_security() -> None:
    site = Site([Route("/safe", Page("Safe"))])

    with pytest.raises(InvalidRoutePathError):
        site.route("/safe/../admin")


def test_site_membership_check_inherits_route_path_security() -> None:
    site = Site([Route("/safe", Page("Safe"))])

    with pytest.raises(InvalidRoutePathError):
        site.has_route("/safe/%2e%2e/admin")


def test_sitemap_is_a_domain_projection_not_xml_output() -> None:
    site = Site([Route("/", Page("Home"))])

    assert site.sitemap.paths == ("/",)
    assert not hasattr(site.sitemap, "render")
    assert not hasattr(site.sitemap, "write")
    assert not hasattr(site.sitemap, "to_xml")


def test_site_does_not_expose_filesystem_output_paths() -> None:
    route = Route("/docs", Page("Docs"))
    site = Site(
        [route],
        navigation=Navigation([NavigationItem("Docs", route)]),
    )

    assert not hasattr(site, "output_path")
    assert not hasattr(site, "build")
    assert site.route("/docs") is route
