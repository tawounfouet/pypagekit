import pytest

from pypagekit import Container, Heading, Image, Link, Page, Paragraph, Text
from pypagekit.rendering import HtmlRenderer
from pypagekit.rendering.escaping import escape_attribute, escape_text


@pytest.mark.parametrize(
    "payload",
    [
        "<script>alert(1)</script>",
        "<img src=x onerror=alert(1)>",
        "<svg onload=alert(1)>",
        "</textarea><script>alert(1)</script>",
        "<iframe srcdoc='<script>alert(1)</script>'></iframe>",
    ],
)
def test_active_markup_is_inert_in_text_nodes(payload: str) -> None:
    html = HtmlRenderer().render(Text(payload))

    assert "<script" not in html.lower()
    assert "<img" not in html.lower()
    assert "<svg" not in html.lower()
    assert "<iframe" not in html.lower()
    assert "&lt;" in html


@pytest.mark.parametrize(
    "factory",
    [
        lambda payload: Heading(payload),
        lambda payload: Paragraph(payload),
        lambda payload: Link(payload, "/safe"),
    ],
)
def test_text_bearing_elements_escape_xss_payloads(factory: object) -> None:
    payload = '<script>alert("xss")</script>'
    node = factory(payload)  # type: ignore[operator]

    html = HtmlRenderer().render(node)

    assert "<script" not in html.lower()
    assert "&lt;script&gt;" in html


def test_attribute_breakout_payload_in_link_href_is_escaped() -> None:
    href = '/safe" onclick="alert(1)'
    html = HtmlRenderer().render(Link("Safe label", href))

    assert ' onclick="' not in html
    assert "&quot; onclick=&quot;" in html


def test_attribute_breakout_payload_in_image_alt_is_escaped() -> None:
    alt = 'logo" onerror="alert(1)'
    html = HtmlRenderer().render(Image("/safe.png", alt))

    assert ' onerror="' not in html
    assert "&quot; onerror=&quot;" in html


def test_page_title_cannot_break_out_into_markup() -> None:
    page = Page(
        title="</title><script>alert(1)</script>",
        content=[Paragraph("Safe")],
    )

    html = HtmlRenderer().render(page)

    assert "<script" not in html.lower()
    assert "&lt;/title&gt;&lt;script&gt;" in html


def test_nested_composition_does_not_create_an_escape_bypass() -> None:
    payload = "<svg onload=alert(1)>"
    page = Page(
        title="Nested",
        content=[
            Container(
                [
                    Container(
                        [
                            Text(payload),
                            Paragraph(payload),
                        ]
                    )
                ]
            )
        ],
    )

    html = HtmlRenderer().render(page)

    assert "<svg" not in html.lower()
    assert html.count("&lt;svg onload=alert(1)&gt;") == 2


def test_raw_html_api_does_not_exist_on_core_content_types() -> None:
    text = Text("<b>raw?</b>")

    assert not hasattr(text, "raw_html")
    assert not hasattr(text, "escape")
    assert not hasattr(text, "safe")


def test_escape_text_has_no_preescaped_detection() -> None:
    assert escape_text("&lt;script&gt;") == "&amp;lt;script&amp;gt;"


def test_escape_attribute_has_no_preescaped_detection() -> None:
    assert escape_attribute("&quot;") == "&amp;quot;"


def test_domain_value_remains_raw_after_rendering() -> None:
    payload = "<script>alert(1)</script>"
    paragraph = Paragraph(payload)

    HtmlRenderer().render(paragraph)

    assert paragraph.text == payload
