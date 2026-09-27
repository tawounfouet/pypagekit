"""Context-specific HTML escaping primitives."""

from html import escape


def escape_text(value: str) -> str:
    """Escape a semantic string for an HTML text context."""

    if not isinstance(value, str):
        raise TypeError("HTML text value must be a string.")
    return escape(value, quote=False)


def escape_attribute(value: str) -> str:
    """Escape a semantic string for a double-quoted HTML attribute context."""

    if not isinstance(value, str):
        raise TypeError("HTML attribute value must be a string.")
    return escape(value, quote=True)
