from pypagekit import Container, Content, Heading, Node, Page, Paragraph, Text, __version__


def test_package_imports() -> None:
    assert __version__
    assert issubclass(Content, Node)
    assert issubclass(Page, Node)
    assert issubclass(Text, Content)
    assert issubclass(Heading, Content)
    assert issubclass(Paragraph, Content)
    assert issubclass(Container, Content)


def test_current_version() -> None:
    assert __version__ == "0.1.0a4"
