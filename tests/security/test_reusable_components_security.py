import pytest

from pypagekit import Attributes, Link, Paragraph
from pypagekit.components import Card, Hero, Section
from pypagekit.exceptions import UnsafeUrlError
from pypagekit.rendering import HtmlRenderer


def test_section_title_and_children_still_use_html_escaping() -> None:
    section = Section(
        "<script>alert(1)</script>",
        [Paragraph("<svg onload=alert(1)>")],
    )

    html = HtmlRenderer().render(section)

    assert "<script" not in html.lower()
    assert "<svg" not in html.lower()
    assert "&lt;script&gt;" in html
    assert "&lt;svg onload=alert(1)&gt;" in html


def test_reusable_component_attributes_still_use_attribute_escaping() -> None:
    card = Card(
        title="Card",
        attributes=Attributes(
            title='safe" onclick="alert(1)',
        ),
    )

    html = HtmlRenderer().render(card)

    assert ' onclick="' not in html
    assert "&quot; onclick=&quot;" in html


def test_hero_action_still_uses_url_security_policy() -> None:
    hero = Hero(
        "Unsafe",
        action=Link("Click", "javascript:alert(1)"),
    )

    with pytest.raises(UnsafeUrlError):
        HtmlRenderer().render(hero)


def test_reusable_components_expose_no_raw_html_bypass() -> None:
    section = Section("<b>Title</b>")

    assert not hasattr(section, "raw_html")
    assert not hasattr(section, "safe")
    assert not hasattr(section, "escape")
