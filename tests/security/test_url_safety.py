import pytest

from pypagekit import Image, Link
from pypagekit.exceptions import UnsafeUrlError
from pypagekit.rendering import HtmlRenderer
from pypagekit.rendering.security import validate_image_src, validate_link_href


@pytest.mark.parametrize(
    "href",
    [
        "/about",
        "about",
        "./about",
        "../about",
        "#section",
        "?q=python",
        "//cdn.example.com/path",
        "https://example.com",
        "HTTP://example.com",
        "mailto:hello@example.com",
    ],
)
def test_safe_link_destinations_are_accepted(href: str) -> None:
    assert validate_link_href(href) == href


@pytest.mark.parametrize(
    "src",
    [
        "/assets/logo.png",
        "assets/logo.png",
        "./logo.png",
        "../logo.png",
        "//cdn.example.com/logo.png",
        "https://example.com/logo.png",
        "HTTP://example.com/logo.png",
    ],
)
def test_safe_image_sources_are_accepted(src: str) -> None:
    assert validate_image_src(src) == src


@pytest.mark.parametrize(
    "href",
    [
        "javascript:alert(1)",
        "JAVASCRIPT:alert(1)",
        " javascript:alert(1)",
        "java\tscript:alert(1)",
        "java\nscript:alert(1)",
        "vbscript:msgbox(1)",
        "data:text/html,<script>alert(1)</script>",
        "file:///etc/passwd",
        "ftp://example.com/file",
    ],
)
def test_unsafe_link_schemes_are_rejected(href: str) -> None:
    with pytest.raises(UnsafeUrlError):
        validate_link_href(href)


@pytest.mark.parametrize(
    "src",
    [
        "javascript:alert(1)",
        "data:image/svg+xml,<svg onload=alert(1)>",
        "file:///tmp/image.png",
        "mailto:hello@example.com",
        "ftp://example.com/image.png",
    ],
)
def test_unsafe_image_schemes_are_rejected(src: str) -> None:
    with pytest.raises(UnsafeUrlError):
        validate_image_src(src)


@pytest.mark.parametrize(
    "value",
    [
        "https://example.com/\x00bad",
        "https://example.com/\x01bad",
        "https://example.com/\x7fbad",
    ],
)
def test_forbidden_control_characters_are_rejected(value: str) -> None:
    with pytest.raises(UnsafeUrlError, match="control characters"):
        validate_link_href(value)


def test_renderer_rejects_unsafe_link_before_serialization() -> None:
    with pytest.raises(UnsafeUrlError, match="javascript"):
        HtmlRenderer().render(Link("Click me", "javascript:alert(1)"))


def test_renderer_rejects_unsafe_image_before_serialization() -> None:
    with pytest.raises(UnsafeUrlError, match="data"):
        HtmlRenderer().render(
            Image(
                "data:image/svg+xml,<svg onload=alert(1)>",
                "unsafe",
            )
        )


def test_renderer_preserves_safe_url_value_then_attribute_escapes_it() -> None:
    html = HtmlRenderer().render(
        Link(
            "Docs",
            'https://example.com/?a=1&b="two"',
        )
    )

    assert html == ('<a href="https://example.com/?a=1&amp;b=&quot;two&quot;">Docs</a>')


@pytest.mark.parametrize(
    "value",
    [
        "javascript%3Aalert(1)",
        "java%0Ascript:alert(1)",
        "https://example.com/%00bad",
        "https://example.com/%7Fbad",
        "https://example.com/%ZZbad",
    ],
)
def test_percent_encoded_url_ambiguity_is_rejected(value: str) -> None:
    with pytest.raises(UnsafeUrlError):
        validate_link_href(value)


def test_percent_encoded_safe_https_scheme_is_accepted() -> None:
    value = "https%3A//example.com/docs"

    assert validate_link_href(value) == value
