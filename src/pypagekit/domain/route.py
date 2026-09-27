"""Logical URL routes for page placement."""

import re
from dataclasses import dataclass
from urllib.parse import unquote, urlsplit

from pypagekit.exceptions import InvalidRoutePageError, InvalidRoutePathError

from .page import Page

_PERCENT_ESCAPE_RE = re.compile(r"%(?![0-9A-Fa-f]{2})")
_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def normalize_route_path(path: str) -> str:
    """Validate and canonicalize an internal logical route path."""

    if not isinstance(path, str):
        raise TypeError("Route path must be a string.")
    if not path:
        raise InvalidRoutePathError("Route path must not be empty.")
    if _CONTROL_RE.search(path):
        raise InvalidRoutePathError("Route path must not contain control characters.")
    if "\\" in path:
        raise InvalidRoutePathError("Route path must use forward slashes only.")
    if _PERCENT_ESCAPE_RE.search(path):
        raise InvalidRoutePathError("Route path contains an invalid percent escape.")
    if "?" in path:
        raise InvalidRoutePathError("Route path must not contain a query string.")
    if "#" in path:
        raise InvalidRoutePathError("Route path must not contain a fragment.")

    parsed = urlsplit(path)
    if parsed.scheme or parsed.netloc:
        raise InvalidRoutePathError("Route path must be internal, not an external URL.")
    if not parsed.path.startswith("/"):
        raise InvalidRoutePathError("Route path must be absolute and start with '/'.")
    if parsed.path.startswith("//"):
        raise InvalidRoutePathError("Route path must not be protocol-relative.")
    if "//" in parsed.path:
        raise InvalidRoutePathError("Route path must not contain empty path segments.")

    decoded_path = unquote(parsed.path)
    if _CONTROL_RE.search(decoded_path):
        raise InvalidRoutePathError("Route path must not encode control characters.")
    if "\\" in decoded_path:
        raise InvalidRoutePathError("Route path must not encode backslash separators.")
    if decoded_path.count("/") != parsed.path.count("/"):
        raise InvalidRoutePathError("Route path must not encode slash separators.")

    decoded_segments = decoded_path.split("/")
    if any(segment in {".", ".."} for segment in decoded_segments):
        raise InvalidRoutePathError("Route path must not contain '.' or '..' segments.")

    if parsed.path == "/":
        return "/"

    return parsed.path.rstrip("/")


@dataclass(frozen=True, slots=True, init=False)
class Route:
    """Immutable association between a canonical logical path and a Page."""

    path: str
    page: Page

    def __init__(self, path: str, page: Page) -> None:
        if not isinstance(page, Page):
            raise InvalidRoutePageError("Route page must be a Page object.")

        object.__setattr__(self, "path", normalize_route_path(path))
        object.__setattr__(self, "page", page)

    @property
    def is_root(self) -> bool:
        """Return whether this route represents the site root."""

        return self.path == "/"

    @property
    def segments(self) -> tuple[str, ...]:
        """Return the canonical path segments in declaration order."""

        if self.is_root:
            return ()
        return tuple(self.path.removeprefix("/").split("/"))
