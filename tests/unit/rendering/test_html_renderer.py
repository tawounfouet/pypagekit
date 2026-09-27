import pytest

from pypagekit import (
    Container,
    Heading,
    Image,
    Link,
    Node,
    Paragraph,
    Text,
)
from pypagekit.exceptions import UnsupportedNodeError
from pypagekit.rendering import HtmlRenderer, Renderer


def test_html_renderer_satisfies_renderer_protocol_shape() -> None:
    renderer: Renderer = HtmlRenderer()

    assert renderer.render(Text("Hello")) == "Hello"


def test_text_renders_as_escaped_text_fragment() -> None:
    renderer = HtmlRenderer()

    assert renderer.render(Text("<strong>A & B</strong>")) == (
        "&lt;strong&gt;A &amp; B&lt;/strong&gt;"
    )


@pytest.mark.parametrize(
    ("level", "expected"),
    [
        (1, "<h1>Title</h1>"),
        (2, "<h2>Title</h2>"),
        (3, "<h3>Title</h3>"),
        (4, "<h4>Title</h4>"),
        (5, "<h5>Title</h5>"),
        (6, "<h6>Title</h6>"),
    ],
)
def test_heading_maps_level_to_semantic_heading_tag(
    level: int,
    expected: str,
) -> None:
    renderer = HtmlRenderer()

    assert renderer.render(Heading("Title", level=level)) == expected


def test_heading_text_is_escaped() -> None:
    renderer = HtmlRenderer()

    assert renderer.render(Heading("A & <B>")) == "<h1>A &amp; &lt;B&gt;</h1>"


def test_paragraph_renders_with_escaped_text() -> None:
    renderer = HtmlRenderer()

    assert renderer.render(Paragraph('A & "B" <C>')) == (
        '<p>A &amp; "B" &lt;C&gt;</p>'
    )


def test_container_renders_children_recursively_in_order() -> None:
    renderer = HtmlRenderer()
    container = Container(
        [
            Heading("First"),
            Paragraph("Second"),
            Text("Third"),
        ]
    )

    assert renderer.render(container) == (
        "<div><h1>First</h1><p>Second</p>Third</div>"
    )


def test_nested_containers_render_recursively() -> None:
    renderer = HtmlRenderer()
    tree = Container(
        [
            Text("A"),
            Container(
                [
                    Text("B"),
                    Container([Text("C")]),
                ]
            ),
        ]
    )

    assert renderer.render(tree) == "<div>A<div>B<div>C</div></div></div>"


def test_empty_container_renders_empty_div() -> None:
    assert HtmlRenderer().render(Container()) == "<div></div>"


def test_link_renders_escaped_label_and_attribute() -> None:
    renderer = HtmlRenderer()
    link = Link(
        label='A & "B" <C>',
        href='/docs?a=1&b="two"',
    )

    assert renderer.render(link) == (
        '<a href="/docs?a=1&amp;b=&quot;two&quot;">'
        'A &amp; "B" &lt;C&gt;</a>'
    )


def test_image_renders_as_void_element() -> None:
    renderer = HtmlRenderer()
    image = Image(
        src='/assets/logo?a=1&b="two"',
        alt='A & "logo"',
    )

    assert renderer.render(image) == (
        '<img alt="A &amp; &quot;logo&quot;" '
        'src="/assets/logo?a=1&amp;b=&quot;two&quot;">'
    )


def test_decorative_image_preserves_empty_alt() -> None:
    renderer = HtmlRenderer()

    assert renderer.render(Image("/decorative.png", "")) == (
        '<img alt="" src="/decorative.png">'
    )


def test_renderer_preserves_unicode() -> None:
    renderer = HtmlRenderer()

    assert renderer.render(Paragraph("Café 東京 你好 🔥")) == (
        "<p>Café 東京 你好 🔥</p>"
    )


def test_renderer_rejects_unknown_node_type() -> None:
    class UnknownNode(Node):
        pass

    with pytest.raises(UnsupportedNodeError, match="UnknownNode"):
        HtmlRenderer().render(UnknownNode())


def test_rendering_same_node_twice_is_deterministic() -> None:
    renderer = HtmlRenderer()
    node = Container(
        [
            Heading("Title"),
            Paragraph("Body"),
            Link("Home", "/"),
        ]
    )

    assert renderer.render(node) == renderer.render(node)


def test_rendering_does_not_mutate_domain_objects() -> None:
    renderer = HtmlRenderer()
    paragraph = Paragraph("A & B")
    container = Container([paragraph])

    renderer.render(container)

    assert paragraph.text == "A & B"
    assert container.children == (paragraph,)
