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


def test_page_description_renders_as_meta_description() -> None:
    page = Page(
        title="Metadata",
        description="A concise page description.",
    )

    assert HtmlRenderer().render(page) == (
        '<!DOCTYPE html><html lang="en"><head><meta charset="utf-8">'
        '<title>Metadata</title><meta content="A concise page description." '
        'name="description"></head><body></body></html>'
    )


def test_page_description_is_attribute_escaped() -> None:
    page = Page(
        title="Metadata",
        description='A & "quoted" <description>',
    )

    html = HtmlRenderer().render(page)

    assert (
        '<meta content="A &amp; &quot;quoted&quot; &lt;description&gt;" name="description">'
    ) in html


def test_empty_page_description_is_preserved() -> None:
    page = Page(
        title="Metadata",
        description="",
    )

    assert '<meta content="" name="description">' in HtmlRenderer().render(page)


def test_absent_page_description_emits_no_description_meta() -> None:
    page = Page(title="Metadata")

    html = HtmlRenderer().render(page)

    assert 'name="description"' not in html


def test_head_metadata_order_is_deterministic() -> None:
    page = Page(
        title="Metadata",
        description="Description",
    )

    html = HtmlRenderer().render(page)

    charset_index = html.index('<meta charset="utf-8">')
    title_index = html.index("<title>Metadata</title>")
    description_index = html.index('<meta content="Description" name="description">')

    assert charset_index < title_index < description_index


def test_page_rendering_is_deterministic() -> None:
    page = Page(
        title="Stable",
        description="Stable metadata",
        content=[
            Heading("Heading"),
            Paragraph("Paragraph"),
        ],
    )
    renderer = HtmlRenderer()

    assert renderer.render(page) == renderer.render(page)
