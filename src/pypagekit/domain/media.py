"""Media content primitives for the PyPageKit domain."""

from dataclasses import dataclass, field

from pypagekit.exceptions import InvalidImageSourceError

from .attributes import Attributes
from .base import Content


class Media(Content):
    """Base type for media content embedded in a page tree."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Image(Media):
    """Image media with a source reference and required alternative text."""

    src: str
    alt: str
    attributes: Attributes = field(default_factory=Attributes, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.src, str):
            raise TypeError("Image src must be a string.")
        if not self.src.strip():
            raise InvalidImageSourceError("Image src must not be empty.")
        if not isinstance(self.alt, str):
            raise TypeError("Image alt must be a string.")
        if not isinstance(self.attributes, Attributes):
            raise TypeError("Image attributes must be an Attributes object.")
