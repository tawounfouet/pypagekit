from pypagekit import (
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
from pypagekit.exceptions import RenderingError, SerializationError


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
    assert issubclass(SerializationError, RenderingError)


def test_current_version() -> None:
    assert __version__ == "0.2.0a1"
