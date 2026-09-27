from pathlib import Path, PurePosixPath\n\nfrom pypagekit import (
    Asset,
    Assets,
    Attributes,
    Component,
    ComponentRef,
    Container,
    Content,
    Fragment,
    Heading,
    Image,
    Layout,
    LayoutRegion,
    Link,
    Navigation,
    NavigationItem,
    Node,
    Page,
    Paragraph,
    Route,
    Site,
    Sitemap,
    SitemapEntry,
    Slot,
    SlotBindings,
    SlottedComponent,
    Text,
    __version__,
)
from pypagekit.components import Card, ComponentRegistry, ComponentRuntime, Hero, Section
from pypagekit.domain import Action, Media
from pypagekit.exceptions import (
    ComponentError,
    ComponentRegistryError,
    DuplicateAssetTargetError,
    DuplicateComponentRegistrationError,
    InvalidAssetError,
    InvalidAttributeError,
    InvalidComponentNameError,
    InvalidLayoutError,
    InvalidNavigationError,
    InvalidRegisteredComponentError,
    InvalidRouteError,
    InvalidSiteError,
    InvalidSlotError,
    MissingComponentRegistryError,
    RenderingError,
    SecurityError,
    SerializationError,
    UnknownComponentError,
    UnresolvedSlotError,
    UnsafeUrlError,
    UnsupportedNodeError,
)
from pypagekit.rendering import HtmlRenderer, Renderer


def test_package_imports() -> None:
    assert __version__
    asset = Asset(Path("logo.png"), PurePosixPath("assets/logo.png"))
    assert isinstance(asset, Asset)
    assert isinstance(Assets([asset]), Assets)
    assert issubclass(Content, Node)
    assert issubclass(Page, Node)
    root_route = Route("/", Page("Root"))
    assert isinstance(root_route, Route)
    assert isinstance(Site([root_route]), Site)
    assert isinstance(Sitemap([root_route]), Sitemap)
    assert isinstance(SitemapEntry(root_route), SitemapEntry)
    assert issubclass(Component, Content)
    assert issubclass(ComponentRef, Content)
    assert issubclass(Layout, Component)
    assert issubclass(LayoutRegion, Content)
    assert isinstance(Navigation(), Navigation)
    assert isinstance(NavigationItem("Root", Route("/", Page("Root"))), NavigationItem)
    assert issubclass(Fragment, Content)
    assert issubclass(Slot, Content)
    assert issubclass(SlottedComponent, Component)
    assert isinstance(SlotBindings(), SlotBindings)
    assert issubclass(Text, Content)
    assert issubclass(Heading, Content)
    assert issubclass(Paragraph, Content)
    assert issubclass(Container, Content)
    assert issubclass(Action, Content)
    assert issubclass(Link, Action)
    assert issubclass(Media, Content)
    assert issubclass(Image, Media)
    assert isinstance(Attributes(), Attributes)
    assert isinstance(ComponentRuntime(), ComponentRuntime)
    assert isinstance(ComponentRegistry(), ComponentRegistry)
    assert issubclass(Section, Component)
    assert issubclass(Card, Component)
    assert issubclass(Hero, Component)
    assert issubclass(DuplicateAssetTargetError, InvalidAssetError)
    assert issubclass(ComponentError, Exception)
    assert issubclass(ComponentRegistryError, ComponentError)
    assert issubclass(DuplicateComponentRegistrationError, ComponentRegistryError)
    assert issubclass(InvalidComponentNameError, ComponentRegistryError)
    assert issubclass(InvalidRegisteredComponentError, ComponentRegistryError)
    assert issubclass(InvalidRouteError, Exception)
    assert issubclass(InvalidSiteError, Exception)
    assert issubclass(MissingComponentRegistryError, ComponentRegistryError)
    assert issubclass(UnknownComponentError, ComponentRegistryError)
    assert issubclass(InvalidLayoutError, Exception)
    assert issubclass(InvalidNavigationError, Exception)
    assert issubclass(InvalidSlotError, Exception)
    assert issubclass(UnresolvedSlotError, InvalidSlotError)
    assert issubclass(SerializationError, RenderingError)
    assert issubclass(SecurityError, RenderingError)
    assert issubclass(UnsafeUrlError, SecurityError)
    assert issubclass(InvalidAttributeError, Exception)
    assert issubclass(UnsupportedNodeError, RenderingError)

    renderer: Renderer = HtmlRenderer()
    assert isinstance(renderer, HtmlRenderer)


def test_current_version() -> None:
    assert __version__ == "0.5.0a1"
