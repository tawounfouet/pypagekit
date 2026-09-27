import pytest

from pypagekit import Navigation, NavigationItem, Page, Route
from pypagekit.exceptions import InvalidRoutePathError


def test_navigation_label_remains_raw_semantic_text() -> None:
    label = '<script>alert("x")</script>'
    item = NavigationItem(label, Route("/safe", Page("Safe")))

    assert item.label == label
    assert Navigation([item]).items == (item,)


@pytest.mark.parametrize(
    "path",
    [
        "//evil.example/path",
        "/safe/../admin",
        "/safe/%2e%2e/admin",
        "/safe?next=https://evil.example",
        "/safe#<script>",
    ],
)
def test_navigation_cannot_bypass_route_security(path: str) -> None:
    with pytest.raises(InvalidRoutePathError):
        NavigationItem("Unsafe", Route(path, Page("Unsafe")))


def test_navigation_does_not_generate_or_interpret_html() -> None:
    item = NavigationItem("<b>Docs</b>", Route("/docs", Page("Docs")))
    navigation = Navigation([item])

    assert navigation.walk()[0].label == "<b>Docs</b>"
    assert not hasattr(navigation, "render")
