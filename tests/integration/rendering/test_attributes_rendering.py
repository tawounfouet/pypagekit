from pypagekit import Attributes, Container, Heading, Image, Link, Paragraph
from pypagekit.rendering import HtmlRenderer


def test_heading_renders_controlled_attributes() -> None:
    heading = Heading(
        "Title",
        attributes=Attributes(
            id="hero",
            classes=["display", "wide"],
            title="Heading title",
            data={"testid": "hero"},
            aria={"label": "Main heading"},
        ),
    )

    assert HtmlRenderer().render(heading) == (
        '<h1 aria-label="Main heading" class="display wide" data-testid="hero" '
        'id="hero" title="Heading title">Title</h1>'
    )


def test_paragraph_renders_controlled_attributes() -> None:
    paragraph = Paragraph(
        "Body",
        attributes=Attributes(classes=["copy"], data={"kind": "intro"}),
    )

    assert HtmlRenderer().render(paragraph) == ('<p class="copy" data-kind="intro">Body</p>')


def test_container_renders_attributes_and_children() -> None:
    container = Container(
        [Paragraph("Body")],
        attributes=Attributes(id="content", classes=["stack"]),
    )

    assert HtmlRenderer().render(container) == ('<div class="stack" id="content"><p>Body</p></div>')


def test_link_combines_intrinsic_href_with_controlled_attributes() -> None:
    link = Link(
        "About",
        "/about",
        attributes=Attributes(
            id="about-link",
            classes=["nav-link"],
            aria={"label": "About page"},
        ),
    )

    assert HtmlRenderer().render(link) == (
        '<a aria-label="About page" class="nav-link" href="/about" id="about-link">About</a>'
    )


def test_image_combines_intrinsic_attributes_with_controlled_attributes() -> None:
    image = Image(
        "/logo.png",
        "Logo",
        attributes=Attributes(
            classes=["brand"],
            data={"role": "logo"},
        ),
    )

    assert HtmlRenderer().render(image) == (
        '<img alt="Logo" class="brand" data-role="logo" src="/logo.png">'
    )


def test_default_attributes_do_not_change_existing_output() -> None:
    assert HtmlRenderer().render(Heading("Title")) == "<h1>Title</h1>"
    assert HtmlRenderer().render(Paragraph("Body")) == "<p>Body</p>"
    assert HtmlRenderer().render(Container()) == "<div></div>"
    assert HtmlRenderer().render(Link("Home", "/")) == '<a href="/">Home</a>'
    assert HtmlRenderer().render(Image("/logo.png", "Logo")) == ('<img alt="Logo" src="/logo.png">')


def test_attribute_output_is_deterministic() -> None:
    first = Heading(
        "Title",
        attributes=Attributes(
            data={"zeta": "2", "alpha": "1"},
            aria={"label": "Title", "hidden": "false"},
            classes=["one", "two"],
            id="heading",
        ),
    )
    second = Heading(
        "Title",
        attributes=Attributes(
            data={"alpha": "1", "zeta": "2"},
            aria={"hidden": "false", "label": "Title"},
            classes=["one", "two"],
            id="heading",
        ),
    )

    assert HtmlRenderer().render(first) == HtmlRenderer().render(second)
