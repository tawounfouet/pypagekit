"""HTML renderer for the PyPageKit domain."""

from pypagekit.domain import (
    Container,
    Heading,
    Image,
    Link,
    Node,
    Page,
    Paragraph,
    Text,
)
from pypagekit.exceptions import UnsupportedNodeError

from .escaping import escape_text
from .security import validate_image_src, validate_link_href
from .serializer import serialize_doctype, serialize_element, serialize_void_element


class HtmlRenderer:
    """Render PyPageKit domain nodes into deterministic HTML5 strings."""

    def render(self, node: Node) -> str:
        """Render a supported domain node to HTML."""

        if isinstance(node, Page):
            return self._render_page(node)
        if isinstance(node, Text):
            return escape_text(node.value)
        if isinstance(node, Heading):
            return serialize_element(
                f"h{node.level}",
                content=escape_text(node.text),
            )
        if isinstance(node, Paragraph):
            return serialize_element(
                "p",
                content=escape_text(node.text),
            )
        if isinstance(node, Container):
            return serialize_element(
                "div",
                content=self._render_children(node.children),
            )
        if isinstance(node, Link):
            return serialize_element(
                "a",
                content=escape_text(node.label),
                attributes={"href": validate_link_href(node.href)},
            )
        if isinstance(node, Image):
            return serialize_void_element(
                "img",
                attributes={
                    "src": validate_image_src(node.src),
                    "alt": node.alt,
                },
            )

        raise UnsupportedNodeError(
            f"Unsupported node type for HTML rendering: {type(node).__name__}."
        )

    def _render_page(self, page: Page) -> str:
        body = serialize_element(
            "body",
            content=self._render_children(page.content),
        )
        head = serialize_element(
            "head",
            content=(
                serialize_void_element(
                    "meta",
                    attributes={"charset": "utf-8"},
                )
                + serialize_element(
                    "title",
                    content=escape_text(page.title),
                )
            ),
        )
        document = serialize_element(
            "html",
            content=head + body,
            attributes={"lang": page.lang},
        )

        return serialize_doctype() + document

    def _render_children(self, children: tuple[Node, ...]) -> str:
        return "".join(self.render(child) for child in children)
