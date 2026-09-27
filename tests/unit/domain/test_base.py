from pypagekit import Content, Node


def test_content_is_a_node() -> None:
    assert issubclass(Content, Node)
