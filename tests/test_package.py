from pypagekit import (
    Attributes,
    Container,
    Content,
    Heading,
    Image,
    Link,
    Node,
    Page,
    Paragraph,
    Text,
    __version__,
)
from pypagekit.domain import Action, Media
from pypagekit.exceptions import (
    InvalidAttributeError,
    RenderingError,
    SecurityError,
    SerializationError,
    UnsafeUrlError,
    UnsupportedNodeError,
)
from pypagekit.rendering import HtmlRenderer, Renderer


def test_package_imports() -> None:
    assert __version__
    assert issubclass(Content, Node)
    assert issubclass(Page, Node)
    assert issubclass(Text, Content)
    assert issubclass(Heading, Content)
    assert issubclass(Paragraph, Content)
    assert issubclass(Container, Content)
    assert issubclass(Action, Content)
    assert issubclass(Link, Action)
    assert issubclass(Media, Content)
    assert issubclass(Image, Media)
    assert isinstance(Attributes(), Attributes)
    assert issubclass(SerializationError, RenderingError)
    assert issubclass(SecurityError, RenderingError)
    assert issubclass(UnsafeUrlError, SecurityError)
    assert issubclass(InvalidAttributeError, Exception)
    assert issubclass(UnsupportedNodeError, RenderingError)

    renderer: Renderer = HtmlRenderer()
    assert isinstance(renderer, HtmlRenderer)


def test_current_version() -> None:
    assert __version__ == "0.2.0b3"
