"""Core domain abstractions for PyPageKit."""


class Node:
    """Base type for every node in the PyPageKit domain tree."""

    __slots__ = ()


class Content(Node):
    """Base type for nodes that may appear inside a page content tree."""

    __slots__ = ()
