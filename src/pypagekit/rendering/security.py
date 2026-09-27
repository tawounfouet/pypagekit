"""Security policy for render-time URL references."""

import re

from pypagekit.exceptions import UnsafeUrlError

_LINK_SCHEMES = frozenset({"http", "https", "mailto"})
_IMAGE_SCHEMES = frozenset({"http", "https"})
_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*$")


def validate_link_href(value: str) -> str:
    """Validate a link destination and return the original semantic value."""

    return _validate_url_reference(
        value,
        allowed_schemes=_LINK_SCHEMES,
        context="link href",
    )


def validate_image_src(value: str) -> str:
    """Validate an image source and return the original semantic value."""

    return _validate_url_reference(
        value,
        allowed_schemes=_IMAGE_SCHEMES,
        context="image src",
    )


def _validate_url_reference(
    value: str,
    *,
    allowed_schemes: frozenset[str],
    context: str,
) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{context} must be a string.")

    if _contains_forbidden_control(value):
        raise UnsafeUrlError(f"Unsafe {context}: control characters are not allowed.")

    candidate = value.strip()
    colon_index = candidate.find(":")
    if colon_index < 0:
        return value

    prefix = candidate[:colon_index]
    normalized_prefix = _remove_ascii_whitespace(prefix).lower()

    if not normalized_prefix:
        return value
    if not _SCHEME_RE.fullmatch(normalized_prefix):
        return value
    if normalized_prefix not in allowed_schemes:
        raise UnsafeUrlError(
            f"Unsafe {context}: URL scheme '{normalized_prefix}' is not allowed."
        )

    return value


def _remove_ascii_whitespace(value: str) -> str:
    return "".join(character for character in value if ord(character) > 0x20)


def _contains_forbidden_control(value: str) -> bool:
    return any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)
