"""Pure HTML5 serialization primitives."""

import re
from collections.abc import Mapping
from typing import TypeAlias

from pypagekit.exceptions import (
    InvalidHtmlAttributeNameError,
    InvalidHtmlTagError,
    UnsupportedAttributeValueError,
)

from .escaping import escape_attribute

HtmlAttributeValue: TypeAlias = str | int | float | bool | None

HTML5_DOCTYPE = "<!DOCTYPE html>"

_VOID_ELEMENTS = frozenset(
    {
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    }
)

_UNSUPPORTED_RAW_TEXT_ELEMENTS = frozenset({"script", "style"})

_TAG_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9:-]*$")
_ATTRIBUTE_NAME_RE = re.compile(r"^[A-Za-z_:][A-Za-z0-9_.:-]*$")


def serialize_doctype() -> str:
    """Return the canonical HTML5 doctype."""

    return HTML5_DOCTYPE


def serialize_element(
    name: str,
    *,
    content: str = "",
    attributes: Mapping[str, HtmlAttributeValue] | None = None,
) -> str:
    """Serialize a non-void HTML element from trusted HTML fragments."""

    normalized_name = _validate_tag_name(name)

    if normalized_name in _VOID_ELEMENTS:
        raise InvalidHtmlTagError(
            f"Void element '{normalized_name}' must use serialize_void_element()."
        )
    if normalized_name in _UNSUPPORTED_RAW_TEXT_ELEMENTS:
        raise InvalidHtmlTagError(
            f"Element '{normalized_name}' requires a dedicated serialization context."
        )
    if not isinstance(content, str):
        raise TypeError("HTML element content must be a string.")

    serialized_attributes = _serialize_attributes(attributes)
    return f"<{normalized_name}{serialized_attributes}>{content}</{normalized_name}>"


def serialize_void_element(
    name: str,
    *,
    attributes: Mapping[str, HtmlAttributeValue] | None = None,
) -> str:
    """Serialize a canonical HTML5 void element without a closing tag."""

    normalized_name = _validate_tag_name(name)

    if normalized_name not in _VOID_ELEMENTS:
        raise InvalidHtmlTagError(f"Element '{normalized_name}' is not an HTML5 void element.")

    serialized_attributes = _serialize_attributes(attributes)
    return f"<{normalized_name}{serialized_attributes}>"


def _serialize_attributes(
    attributes: Mapping[str, HtmlAttributeValue] | None,
) -> str:
    if attributes is None:
        return ""
    if not isinstance(attributes, Mapping):
        raise TypeError("HTML attributes must be a mapping or None.")

    names = list(attributes)
    for name in names:
        _validate_attribute_name(name)

    serialized: list[str] = []
    for name in sorted(names):
        value = attributes[name]

        if value is None or value is False:
            continue
        if value is True:
            serialized.append(name)
            continue
        if isinstance(value, str | int | float):
            escaped_value = escape_attribute(str(value))
            serialized.append(f'{name}="{escaped_value}"')
            continue

        raise UnsupportedAttributeValueError(
            f"Unsupported value type for HTML attribute '{name}': {type(value).__name__}."
        )

    if not serialized:
        return ""

    return " " + " ".join(serialized)


def _validate_tag_name(name: str) -> str:
    if not isinstance(name, str):
        raise TypeError("HTML tag name must be a string.")
    if not _TAG_NAME_RE.fullmatch(name):
        raise InvalidHtmlTagError(f"Invalid HTML tag name: {name!r}.")

    return name.lower()


def _validate_attribute_name(name: str) -> None:
    if not isinstance(name, str):
        raise TypeError("HTML attribute name must be a string.")
    if not _ATTRIBUTE_NAME_RE.fullmatch(name):
        raise InvalidHtmlAttributeNameError(f"Invalid HTML attribute name: {name!r}.")
