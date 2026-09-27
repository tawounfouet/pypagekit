import pytest

from pypagekit.exceptions import (
    InvalidHtmlAttributeNameError,
    InvalidHtmlTagError,
    UnsupportedAttributeValueError,
)
from pypagekit.rendering.serializer import (
    HTML5_DOCTYPE,
    serialize_doctype,
    serialize_element,
    serialize_void_element,
)


def test_serialize_doctype_returns_canonical_html5_doctype() -> None:
    assert serialize_doctype() == "<!DOCTYPE html>"
    assert serialize_doctype() == HTML5_DOCTYPE


def test_serialize_empty_element() -> None:
    assert serialize_element("div") == "<div></div>"


def test_serialize_element_preserves_trusted_fragment_content() -> None:
    result = serialize_element(
        "p",
        content="Hello <strong>world</strong>",
    )

    assert result == "<p>Hello <strong>world</strong></p>"


def test_serialize_element_rejects_non_string_content() -> None:
    with pytest.raises(TypeError, match="content must be a string"):
        serialize_element("div", content=42)  # type: ignore[arg-type]


def test_tag_name_is_canonicalized_to_lowercase() -> None:
    assert serialize_element("DIV") == "<div></div>"


def test_serialize_element_serializes_attributes_in_deterministic_order() -> None:
    attributes = {
        "title": "Hello",
        "class": "hero",
        "id": "intro",
    }

    assert serialize_element("section", attributes=attributes) == (
        '<section class="hero" id="intro" title="Hello"></section>'
    )


def test_attribute_order_is_independent_of_mapping_insertion_order() -> None:
    first = {"id": "x", "class": "a"}
    second = {"class": "a", "id": "x"}

    assert serialize_element("div", attributes=first) == serialize_element(
        "div",
        attributes=second,
    )


def test_empty_string_attribute_is_preserved() -> None:
    result = serialize_element("div", attributes={"title": ""})

    assert result == '<div title=""></div>'


def test_none_attribute_is_omitted() -> None:
    assert serialize_element("div", attributes={"title": None}) == "<div></div>"


def test_true_boolean_attribute_is_serialized_by_name_only() -> None:
    result = serialize_element("button", attributes={"disabled": True})

    assert result == "<button disabled></button>"


def test_false_boolean_attribute_is_omitted() -> None:
    result = serialize_element("button", attributes={"disabled": False})

    assert result == "<button></button>"


def test_numeric_attribute_values_are_supported() -> None:
    result = serialize_element(
        "div",
        attributes={
            "data-count": 3,
            "data-ratio": 1.5,
        },
    )

    assert result == '<div data-count="3" data-ratio="1.5"></div>'


def test_attribute_values_are_escaped_once_at_serialization_boundary() -> None:
    result = serialize_element(
        "a",
        attributes={"href": '/docs?a=1&b="two"'},
    )

    assert result == '<a href="/docs?a=1&amp;b=&quot;two&quot;"></a>'


def test_unsupported_attribute_value_is_rejected() -> None:
    with pytest.raises(UnsupportedAttributeValueError, match="list"):
        serialize_element(
            "div",
            attributes={"class": ["a", "b"]},  # type: ignore[dict-item]
        )


def test_attributes_must_be_mapping_or_none() -> None:
    with pytest.raises(TypeError, match="mapping or None"):
        serialize_element(
            "div",
            attributes=[("id", "x")],  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "name",
    ["", "1div", "div class", "<div>", "div/"],
)
def test_invalid_tag_names_are_rejected(name: str) -> None:
    with pytest.raises(InvalidHtmlTagError):
        serialize_element(name)


def test_non_string_tag_name_is_rejected() -> None:
    with pytest.raises(TypeError, match="tag name must be a string"):
        serialize_element(42)  # type: ignore[arg-type]


@pytest.mark.parametrize(
    "name",
    ["", "bad name", "<id>", "data/value"],
)
def test_invalid_attribute_names_are_rejected(name: str) -> None:
    with pytest.raises(InvalidHtmlAttributeNameError):
        serialize_element("div", attributes={name: "value"})


def test_non_string_attribute_name_is_rejected_before_sorting() -> None:
    with pytest.raises(TypeError, match="attribute name must be a string"):
        serialize_element(
            "div",
            attributes={1: "value", "id": "x"},  # type: ignore[dict-item]
        )


def test_data_aria_and_namespaced_attribute_names_are_supported() -> None:
    result = serialize_element(
        "div",
        attributes={
            "aria-label": "Label",
            "data-id": "42",
            "xml:lang": "fr",
        },
    )
    expected = '<div aria-label="Label" data-id="42" xml:lang="fr"></div>'

    assert result == expected


def test_void_element_uses_html5_form_without_closing_tag() -> None:
    result = serialize_void_element(
        "img",
        attributes={
            "src": "/logo.png",
            "alt": "",
        },
    )

    assert result == '<img alt="" src="/logo.png">'


@pytest.mark.parametrize(
    "name",
    [
        "area",
        "base",
        "br",
        "col",
        "embed",
        "hr",
        "img",
        "input",
        "link",
        "meta",
        "source",
        "track",
        "wbr",
    ],
)
def test_all_html5_void_elements_are_supported(name: str) -> None:
    assert serialize_void_element(name).startswith(f"<{name}")


def test_void_element_cannot_use_regular_element_serializer() -> None:
    with pytest.raises(InvalidHtmlTagError, match="serialize_void_element"):
        serialize_element("img")


def test_non_void_element_cannot_use_void_serializer() -> None:
    with pytest.raises(InvalidHtmlTagError, match="not an HTML5 void element"):
        serialize_void_element("div")


@pytest.mark.parametrize("name", ["script", "style"])
def test_raw_text_elements_require_dedicated_serialization_context(
    name: str,
) -> None:
    with pytest.raises(InvalidHtmlTagError, match="dedicated serialization context"):
        serialize_element(name, content="unsafe")


def test_custom_element_style_tag_name_is_supported() -> None:
    assert serialize_element("my-widget") == "<my-widget></my-widget>"


def test_serialization_preserves_unicode_attribute_values() -> None:
    result = serialize_element(
        "div",
        attributes={"title": "Café 東京 🔥"},
    )

    assert result == '<div title="Café 東京 🔥"></div>'
