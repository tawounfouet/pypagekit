"""Text content primitives for the PyPageKit domain."""

from dataclasses import dataclass

from pypagekit.exceptions import InvalidHeadingLevelError

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

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("Heading text must be a string.")
        if not isinstance(self.level, int) or isinstance(self.level, bool):
            raise TypeError("Heading level must be an integer from 1 through 6.")
        if not 1 <= self.level <= 6:
            raise InvalidHeadingLevelError("Heading level must be between 1 and 6.")


@dataclass(frozen=True, slots=True)
class Paragraph(Content):
    """Paragraph text preserved exactly as authored."""

    text: str

    def __post_init__(self) -> None:
        if not isinstance(self.text, str):
            raise TypeError("Paragraph text must be a string.")
