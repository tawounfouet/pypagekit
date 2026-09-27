"""Composition containers for the PyPageKit domain."""

from collections.abc import Iterable
from dataclasses import dataclass

from pypagekit.exceptions import InvalidContainerChildError

from .attributes import Attributes
from .base import Content

_EMPTY_ATTRIBUTES = Attributes()


@dataclass(frozen=True, slots=True, init=False)
class Container(Content):
    """Ordered immutable collection of child content nodes."""

    children: tuple[Content, ...]
    attributes: Attributes

    def __init__(
        self,
        children: Iterable[Content] = (),
        *,
        attributes: Attributes = _EMPTY_ATTRIBUTES,
    ) -> None:
        try:
            normalized_children = tuple(children)
        except TypeError as exc:
            raise TypeError("Container children must be an iterable of Content objects.") from exc

        invalid_children = [
            child for child in normalized_children if not isinstance(child, Content)
        ]
        if invalid_children:
            invalid_type = type(invalid_children[0]).__name__
            message = f"Container children must contain only Content objects; got {invalid_type}."
            raise InvalidContainerChildError(message)

        if not isinstance(attributes, Attributes):
            raise TypeError("Container attributes must be an Attributes object.")

        object.__setattr__(self, "children", normalized_children)
        object.__setattr__(self, "attributes", attributes)
