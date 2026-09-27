import pytest

from pypagekit import Attributes, Heading
from pypagekit.rendering import HtmlRenderer


def test_attribute_values_cannot_break_out_of_their_context() -> None:
    heading = Heading(
        "Safe",
        attributes=Attributes(
            id='hero" onclick="alert(1)',
            classes=['lead"onmouseover="alert(1)'],
            title='<script>alert("x")</script>',
            data={"payload": '" onfocus="alert(1)'},
            aria={"label": '<svg onload="alert(1)">'},
        ),
    )

    html = HtmlRenderer().render(heading)

    assert ' onclick="' not in html
    assert ' onmouseover="' not in html
    assert ' onfocus="' not in html
    assert "<script" not in html.lower()
    assert "<svg" not in html.lower()
    assert "&quot;" in html
    assert "&lt;script&gt;" in html
    assert "&lt;svg" in html


def test_event_like_data_name_remains_namespaced() -> None:
    heading = Heading(
        "Safe",
        attributes=Attributes(data={"onload": "alert(1)"}),
    )

    html = HtmlRenderer().render(heading)

    assert 'data-onload="alert(1)"' in html
    assert ' onload="alert(1)"' not in html


def test_arbitrary_event_handler_keyword_is_not_supported() -> None:
    with pytest.raises(TypeError):
        Attributes(onclick="alert(1)")  # type: ignore[call-arg]
