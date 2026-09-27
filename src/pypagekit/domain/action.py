"""Action content primitives for the PyPageKit domain."""

from dataclasses import dataclass

from pypagekit.exceptions import InvalidLinkHrefError

from .base import Content


class Action(Content):
    """Base type for content representing an explicit user action."""

    __slots__ = ()


@dataclass(frozen=True, slots=True)
class Link(Action):
    """Hyperlink action with a textual label and destination reference."""

    label: str
    href: str

    def __post_init__(self) -> None:
        if not isinstance(self.label, str):
            raise TypeError("Link label must be a string.")
        if not isinstance(self.href, str):
            raise TypeError("Link href must be a string.")
        if not self.href.strip():
            raise InvalidLinkHrefError("Link href must not be empty.")
