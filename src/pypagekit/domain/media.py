"""Media content primitives for the PyPageKit domain."""

from dataclasses import dataclass

from pypagekit.exceptions import InvalidImageSourceError

from .base import Content


class Media(Content):
    """Base type for media content embedded in a page tree."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Image(Media):
    """Image media with a source reference and required alternative text."""

    src: str
    alt: str

    def __post_init__(self) -> None:
        if not isinstance(self.src, str):
            raise TypeError("Image src must be a string.")
        if not self.src.strip():
            raise InvalidImageSourceError("Image src must not be empty.")
        if not isinstance(self.alt, str):
            raise TypeError("Image alt must be a string.")
