"""Renderer protocol for PyPageKit representations."""

from typing import Protocol

from pypagekit.domain import Node


class Renderer(Protocol):
    """Public rendering capability contract."""

    def render(self, node: Node) -> str:
        """Render a domain node to a string representation."""
        ...
