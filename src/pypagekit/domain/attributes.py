"""Controlled author-facing attributes for rendered content."""

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from pypagekit.exceptions import (
    InvalidAriaAttributeNameError,
    InvalidClassTokenError,
    InvalidDataAttributeNameError,
)

_SUFFIX_RE = re.compile(r"^[a-z][a-z0-9-]*$")


@dataclass(frozen=True, slots=True, init=False)
class Attributes:
    """Immutable styling and accessibility hooks for HTML-backed content."""

    id: str | None
    classes: tuple[str, ...]
    title: str | None
    data: tuple[tuple[str, str], ...]
    aria: tuple[tuple[str, str], ...]

    def __init__(
        self,
        *,
        id: str | None = None,
        classes: Iterable[str] = (),
        title: str | None = None,
        data: Mapping[str, str] | None = None,
        aria: Mapping[str, str] | None = None,
    ) -> None:
        if id is not None and not isinstance(id, str):
            raise TypeError("Attribute id must be a string or None.")
        if title is not None and not isinstance(title, str):
            raise TypeError("Attribute title must be a string or None.")

        normalized_classes = _normalize_classes(classes)
        normalized_data = _normalize_named_values(
            data,
            kind="data",
        )
        normalized_aria = _normalize_named_values(
            aria,
            kind="aria",
        )

        object.__setattr__(self, "id", id)
        object.__setattr__(self, "classes", normalized_classes)
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "data", normalized_data)
        object.__setattr__(self, "aria", normalized_aria)


def _normalize_classes(classes: Iterable[str]) -> tuple[str, ...]:
    if isinstance(classes, str):
        raise TypeError("Attribute classes must be an iterable of class-token strings.")

    try:
        normalized = tuple(classes)
    except TypeError as exc:
        raise TypeError("Attribute classes must be an iterable of strings.") from exc

    for token in normalized:
        if not isinstance(token, str):
            raise TypeError("Every class token must be a string.")
        if not token or any(character.isspace() for character in token):
            raise InvalidClassTokenError(
                "Class tokens must be non-empty and contain no whitespace."
            )

    return normalized


def _normalize_named_values(
    values: Mapping[str, str] | None,
    *,
    kind: str,
) -> tuple[tuple[str, str], ...]:
    if values is None:
        return ()
    if not isinstance(values, Mapping):
        raise TypeError(f"{kind} attributes must be a mapping or None.")

    normalized: list[tuple[str, str]] = []
    for name, value in values.items():
        if not isinstance(name, str):
            raise TypeError(f"{kind} attribute names must be strings.")
        if not isinstance(value, str):
            raise TypeError(f"{kind} attribute values must be strings.")

        if name.startswith(f"{kind}-") or not _SUFFIX_RE.fullmatch(name):
            if kind == "data":
                raise InvalidDataAttributeNameError(
                    "Data attribute names must be lowercase suffixes without the 'data-' prefix."
                )
            raise InvalidAriaAttributeNameError(
                "ARIA attribute names must be lowercase suffixes without the 'aria-' prefix."
            )

        normalized.append((name, value))

    return tuple(sorted(normalized))
