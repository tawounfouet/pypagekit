from pypagekit import (
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
    Node,
    Page,
    Paragraph,
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
    DuplicateComponentRegistrationError,
    InvalidComponentNameError,
    InvalidRegisteredComponentError,
    MissingComponentRegistryError,
    UnknownComponentError,
    InvalidAttributeError,
    InvalidLayoutError,
    InvalidSlotError,
    RenderingError,
    SecurityError,
    SerializationError,
    UnresolvedSlotError,
    UnsafeUrlError,
    UnsupportedNodeError,
)
from pypagekit.rendering import HtmlRenderer, Renderer


def test_package_imports() -> None:
    assert __version__
    assert issubclass(Content, Node)
    assert issubclass(Page, Node)
    assert issubclass(Component, Content)
    assert issubclass(ComponentRef, Content)
    assert issubclass(Layout, Component)
    assert issubclass(LayoutRegion, Content)
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
    assert issubclass(ComponentError, Exception)
    assert issubclass(ComponentRegistryError, ComponentError)
    assert issubclass(DuplicateComponentRegistrationError, ComponentRegistryError)
    assert issubclass(InvalidComponentNameError, ComponentRegistryError)
    assert issubclass(InvalidRegisteredComponentError, ComponentRegistryError)
    assert issubclass(MissingComponentRegistryError, ComponentRegistryError)
    assert issubclass(UnknownComponentError, ComponentRegistryError)
    assert issubclass(InvalidLayoutError, Exception)
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
    assert __version__ == "0.3.0b3"
