"""Layout abstractions for structural page composition."""

import re
from abc import ABC, abstractmethod
from collections.abc import Iterable
from dataclasses import dataclass
from typing import final

from pypagekit.exceptions import (
    DuplicateLayoutRegionError,
    InvalidLayoutRegionChildError,
    InvalidLayoutRegionNameError,
    InvalidLayoutRegionResultError,
)

from .attributes import Attributes
from .base import Content
from .component import Component
from .container import Container

_REGION_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
_EMPTY_ATTRIBUTES = Attributes()


@dataclass(frozen=True, slots=True, init=False)
class LayoutRegion(Content):
    """Named structural region containing ordered page content."""

    name: str
    children: tuple[Content, ...]
    attributes: Attributes

    def __init__(
        self,
        name: str,
        children: Iterable[Content] = (),
        *,
        attributes: Attributes = _EMPTY_ATTRIBUTES,
    ) -> None:
        if not isinstance(name, str):
            raise TypeError("Layout region name must be a string.")
        if not _REGION_NAME_RE.fullmatch(name):
            raise InvalidLayoutRegionNameError("Layout region names must use lowercase kebab-case.")

        try:
            normalized_children = tuple(children)
        except TypeError as exc:
            raise TypeError(
                "Layout region children must be an iterable of Content objects."
            ) from exc

        invalid_children = [
            child for child in normalized_children if not isinstance(child, Content)
        ]
        if invalid_children:
            invalid_type = type(invalid_children[0]).__name__
            raise InvalidLayoutRegionChildError(
                f"Layout region children must contain only Content objects; got {invalid_type}."
            )

        if not isinstance(attributes, Attributes):
            raise TypeError("Layout region attributes must be an Attributes object.")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "children", normalized_children)
        object.__setattr__(self, "attributes", attributes)


class Layout(Component, ABC):
    """Component that organizes content into named structural regions."""

    __slots__ = ()

    @abstractmethod
    def regions(self) -> Iterable[LayoutRegion]:
        """Return the ordered regions represented by this layout."""

    @final
    def compose(self) -> Content:
        """Compose validated layout regions into an ordinary content tree."""

        try:
            normalized_regions = tuple(self.regions())
        except TypeError as exc:
            raise TypeError("Layout regions must be an iterable of LayoutRegion objects.") from exc

        invalid_regions = [
            region for region in normalized_regions if not isinstance(region, LayoutRegion)
        ]
        if invalid_regions:
            invalid_type = type(invalid_regions[0]).__name__
            raise InvalidLayoutRegionResultError(
                f"Layout regions must contain only LayoutRegion objects; got {invalid_type}."
            )

        names = [region.name for region in normalized_regions]
        if len(names) != len(set(names)):
            raise DuplicateLayoutRegionError("Layout region names must be unique within a layout.")

        return Container(normalized_regions)
