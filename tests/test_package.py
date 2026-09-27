from pypagekit import Content, Node, Page, __version__


def test_package_imports() -> None:
    assert __version__
    assert issubclass(Content, Node)
    assert issubclass(Page, Node)


def test_current_version() -> None:
    assert __version__ == "0.1.0a2"
