"""Composition containers for the PyPageKit domain."""

from collections.abc import Iterable
from dataclasses import dataclass

from pypagekit.exceptions import InvalidContainerChildError

from .base import Content


@dataclass(frozen=True, slots=True, init=False)
class Container(Content):
    """Ordered immutable collection of child content nodes."""

    children: tuple[Content, ...]

    def __init__(self, children: Iterable[Content] = ()) -> None:
        try:
            normalized_children = tuple(children)
        except TypeError as exc:
            raise TypeError("Container children must be an iterable of Content objects.") from exc

        invalid_children = [
            child for child in normalized_children if not isinstance(child, Content)
        ]
        if invalid_children:
            invalid_type = type(invalid_children[0]).__name__
            raise InvalidContainerChildError(
                "Container children must contain only Content objects; "
                f"got {invalid_type}."
            )

        object.__setattr__(self, "children", normalized_children)
