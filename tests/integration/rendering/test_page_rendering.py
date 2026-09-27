from pypagekit import Container, Heading, Image, Link, Page, Paragraph
from pypagekit.rendering import HtmlRenderer


def test_page_renders_complete_compact_html5_document() -> None:
    page = Page(
        title="Home & Docs",
        lang="fr",
        content=[
            Container(
                [
                    Heading("Bienvenue <PyPageKit>"),
                    Paragraph("A & B"),
                    Link("About", "/about"),
                    Image("/assets/logo.png", "Logo"),
                ]
            )
        ],
    )

    html = HtmlRenderer().render(page)

    assert html == (
        '<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">'
        "<title>Home &amp; Docs</title></head><body>"
        "<div><h1>Bienvenue &lt;PyPageKit&gt;</h1><p>A &amp; B</p>"
        '<a href="/about">About</a><img alt="Logo" src="/assets/logo.png">'
        "</div></body></html>"
    )


def test_empty_page_renders_valid_document_shell() -> None:
    page = Page(title="Empty")

    assert HtmlRenderer().render(page) == (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        "<title>Empty</title></head><body></body></html>"
    )


def test_page_rendering_is_deterministic() -> None:
    page = Page(
        title="Stable",
        content=[
            Heading("Heading"),
            Paragraph("Paragraph"),
        ],
    )
    renderer = HtmlRenderer()

    assert renderer.render(page) == renderer.render(page)


def test_page_description_is_not_yet_part_of_lot_07_output_contract() -> None:
    page = Page(
        title="Metadata Later",
        description="Introduced into the HTML head in LOT-09.",
    )

    html = HtmlRenderer().render(page)

    assert "Metadata Later" in html
    assert "Introduced into the HTML head in LOT-09." not in html
