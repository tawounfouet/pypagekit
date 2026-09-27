from pypagekit import Container, Image, Link, Page


def test_link_and_image_can_be_composed_in_container() -> None:
    link = Link(label="About", href="/about")
    image = Image(src="/assets/logo.png", alt="Logo")

    container = Container([link, image])

    assert container.children == (link, image)


def test_link_and_image_can_be_used_directly_in_page() -> None:
    link = Link(label="Home", href="/")
    image = Image(src="/assets/hero.png", alt="Hero")

    page = Page(title="Media", content=[link, image])

    assert page.content == (link, image)
