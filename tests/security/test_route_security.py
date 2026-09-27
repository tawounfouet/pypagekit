import pytest

from pypagekit import Page, Route
from pypagekit.exceptions import InvalidRoutePathError


@pytest.mark.parametrize(
    "path",
    [
        "//evil.example/steal",
        "/safe/../../admin",
        "/safe/%2e%2e/admin",
        "/safe/%2Fadmin",
        "/safe/%5Cadmin",
        "/safe%00admin",
        "/safe?next=https://evil.example",
        "/safe#<script>alert(1)</script>",
    ],
)
def test_route_rejects_externalization_and_path_confusion(path: str) -> None:
    with pytest.raises(InvalidRoutePathError):
        Route(path, Page("Safe"))


def test_route_path_is_not_interpreted_as_html() -> None:
    route = Route("/%3Cscript%3E", Page("Safe"))

    assert route.path == "/%3Cscript%3E"
