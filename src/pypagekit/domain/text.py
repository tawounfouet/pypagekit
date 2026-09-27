"""Text content primitives for the PyPageKit domain."""

from dataclasses import dataclass, field

from pypagekit.exceptions import InvalidHeadingLevelError

from .attributes import Attributes
from .base import Content


@dataclass(frozen=True, slots=True)
class Text(Content):
    """Literal text content preserved exactly as authored."""

    value: str

    def __post_init__(self) -> None:
        if not isinstance(self.value, str):
            raise TypeError("Text value must be a string.")


@dataclass(frozen=True, slots=True)
class Heading(Content):
    """Semantic heading with an HTML-compatible level from 1 through 6."""

    text: str
    level: int = 1
    attributes: Attributes = field(default_factory=Attributes, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("Heading text must be a string.")
        if not isinstance(self.level, int) or isinstance(self.level, bool):
            raise TypeError("Heading level must be an integer from 1 through 6.")
        if not 1 <= self.level <= 6:
            raise InvalidHeadingLevelError("Heading level must be between 1 and 6.")
        if not isinstance(self.attributes, Attributes):
            raise TypeError("Heading attributes must be an Attributes object.")


@dataclass(frozen=True, slots=True)
class Paragraph(Content):
    """Paragraph text preserved exactly as authored."""

    text: str
    attributes: Attributes = field(default_factory=Attributes, kw_only=True)

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("Paragraph text must be a string.")
        if not isinstance(self.attributes, Attributes):
            raise TypeError("Paragraph attributes must be an Attributes object.")
