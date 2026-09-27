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


def test_current_version() -> None:
    assert __version__ == "0.1.0b1"
