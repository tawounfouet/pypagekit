from dataclasses import FrozenInstanceError

import pytest

from pypagekit import Attributes
from pypagekit.exceptions import (
    InvalidAriaAttributeNameError,
    InvalidClassTokenError,
    InvalidDataAttributeNameError,
)


def test_attributes_default_to_empty_values() -> None:
    attributes = Attributes()

    assert attributes.id is None
    assert attributes.classes == ()
    assert attributes.title is None
    assert attributes.data == ()
    assert attributes.aria == ()


def test_attributes_preserve_id_title_and_class_order() -> None:
    attributes = Attributes(
        id="hero",
        classes=["lead", "wide"],
        title="Hero section",
    )

    assert attributes.id == "hero"
    assert attributes.classes == ("lead", "wide")
    assert attributes.title == "Hero section"


def test_data_and_aria_values_are_sorted_by_name() -> None:
    attributes = Attributes(
        data={"zeta": "2", "alpha": "1"},
        aria={"label": "Hero", "hidden": "false"},
    )

    assert attributes.data == (("alpha", "1"), ("zeta", "2"))
    assert attributes.aria == (("hidden", "false"), ("label", "Hero"))


def test_attribute_values_are_not_html_escaped_in_domain() -> None:
    attributes = Attributes(
        id='x"y',
        title="<unsafe>",
        data={"payload": '"quoted" & raw'},
        aria={"label": "<label>"},
    )

    assert attributes.id == 'x"y'
    assert attributes.title == "<unsafe>"
    assert attributes.data == (("payload", '"quoted" & raw'),)
    assert attributes.aria == (("label", "<label>"),)


@pytest.mark.parametrize("classes", [[""], ["two words"], ["tab\tclass"], ["line\nclass"]])
def test_invalid_class_tokens_are_rejected(classes: list[str]) -> None:
    with pytest.raises(InvalidClassTokenError):
        Attributes(classes=classes)


def test_non_string_class_token_is_rejected() -> None:
    with pytest.raises(TypeError, match="class token"):
        Attributes(classes=["valid", 42])  # type: ignore[list-item]


@pytest.mark.parametrize(
    "name",
    ["data-user", "User", "_user", "user_name", "user--name"],
)
def test_invalid_data_attribute_names_are_rejected(name: str) -> None:
    with pytest.raises(InvalidDataAttributeNameError):
        Attributes(data={name: "value"})


@pytest.mark.parametrize(
    "name",
    ["aria-label", "Label", "_label", "aria_label", "label--name"],
)
def test_invalid_aria_attribute_names_are_rejected(name: str) -> None:
    with pytest.raises(InvalidAriaAttributeNameError):
        Attributes(aria={name: "value"})


def test_non_mapping_data_is_rejected() -> None:
    with pytest.raises(TypeError, match="mapping"):
        Attributes(data=[("name", "value")])  # type: ignore[arg-type]


def test_non_string_data_value_is_rejected() -> None:
    with pytest.raises(TypeError, match="values must be strings"):
        Attributes(data={"count": 3})  # type: ignore[dict-item]


def test_non_string_aria_value_is_rejected() -> None:
    with pytest.raises(TypeError, match="values must be strings"):
        Attributes(aria={"hidden": True})  # type: ignore[dict-item]


def test_non_string_id_is_rejected() -> None:
    with pytest.raises(TypeError, match="id must be a string or None"):
        Attributes(id=42)  # type: ignore[arg-type]


def test_non_string_title_is_rejected() -> None:
    with pytest.raises(TypeError, match="title must be a string or None"):
        Attributes(title=42)  # type: ignore[arg-type]


def test_attributes_are_immutable() -> None:
    attributes = Attributes(id="hero")

    with pytest.raises(FrozenInstanceError):
        attributes.id = "changed"  # type: ignore[misc]


def test_arbitrary_style_keyword_is_not_supported() -> None:
    with pytest.raises(TypeError):
        Attributes(style="color:red")  # type: ignore[call-arg]


def test_bare_string_classes_are_rejected() -> None:
    with pytest.raises(TypeError, match="iterable of class-token strings"):
        Attributes(classes="hero")
