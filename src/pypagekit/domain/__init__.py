"""Public core-domain API for PyPageKit."""

from .action import Action, Link
from .attributes import Attributes
from .base import Content, Node
from .component import Component
from .container import Container
from .layout import Layout, LayoutRegion
from .media import Image, Media
from .navigation import Navigation, NavigationItem
from .page import Page
from .reference import ComponentRef
from .route import Route, normalize_route_path
from .site import Site, Sitemap, SitemapEntry
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
    "Navigation",
    "NavigationItem",
    "Node",
    "Page",
    "Paragraph",
    "Route",
    "Site",
    "Sitemap",
    "SitemapEntry",
    "Slot",
    "SlotBindings",
    "SlottedComponent",
    "Text",
    "bind_slots",
    "normalize_route_path",
]
