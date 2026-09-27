"""Public core-domain API for PyPageKit."""

from .action import Action, Link
from .attributes import Attributes
from .base import Content, Node
from .component import Component
from .container import Container
from .layout import Layout, LayoutRegion
from .media import Image, Media
from .page import Page
from .reference import ComponentRef
from .slots import Fragment, Slot, SlotBindings, SlottedComponent, bind_slots
from .text import Heading, Paragraph, Text

__all__ = [
    "Action",
    "Attributes",
    "Component",
    "ComponentRef",
    "Container",
    "Content",
    "Fragment",
    "Heading",
    "Image",
    "Layout",
    "LayoutRegion",
    "Link",
    "Media",
    "Node",
    "Page",
    "Paragraph",
    "Slot",
    "SlotBindings",
    "SlottedComponent",
    "Text",
    "bind_slots",
]
