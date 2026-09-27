"""Component abstraction for reusable domain composition."""

from abc import ABC, abstractmethod

from .base import Content


class Component(Content, ABC):
    """Content node that composes itself into ordinary PyPageKit content."""

    __slots__ = ()

    @abstractmethod
    def compose(self) -> Content:
        """Return the content tree represented by this component."""
