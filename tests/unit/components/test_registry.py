from dataclasses import FrozenInstanceError, dataclass

import pytest

from pypagekit import Component, ComponentRef, Content, Paragraph
from pypagekit.components import ComponentRegistry
from pypagekit.exceptions import (
    DuplicateComponentRegistrationError,
    InvalidComponentNameError,
    InvalidComponentPropertyError,
    InvalidRegisteredComponentError,
    UnknownComponentError,
)


@dataclass(frozen=True, slots=True)
class Message(Component):
    text: str

    def compose(self) -> Content:
        return Paragraph(self.text)


def test_component_ref_normalizes_props_deterministically() -> None:
    ref = ComponentRef("message", {"zeta": 2, "alpha": 1})

    assert ref.name == "message"
    assert ref.props == (("alpha", 1), ("zeta", 2))
    assert ref.as_kwargs() == {"alpha": 1, "zeta": 2}


@pytest.mark.parametrize("name", ["", "Message", "bad_name", "-bad", "bad--name"])
def test_component_ref_rejects_invalid_names(name: str) -> None:
    with pytest.raises(InvalidComponentNameError):
        ComponentRef(name)


@pytest.mark.parametrize("name", ["bad-name", "class", "two words"])
def test_component_ref_rejects_invalid_property_names(name: str) -> None:
    with pytest.raises(InvalidComponentPropertyError):
        ComponentRef("message", {name: "value"})


def test_component_ref_is_immutable() -> None:
    ref = ComponentRef("message")

    with pytest.raises(FrozenInstanceError):
        ref.name = "other"  # type: ignore[misc]


def test_registry_names_are_deterministic() -> None:
    registry = ComponentRegistry({"zeta": Message, "alpha": Message})

    assert registry.names == ("alpha", "zeta")


def test_register_returns_new_registry_without_mutating_original() -> None:
    original = ComponentRegistry()
    updated = original.register("message", Message)

    assert original.names == ()
    assert updated.names == ("message",)


def test_duplicate_registration_is_rejected() -> None:
    registry = ComponentRegistry({"message": Message})

    with pytest.raises(DuplicateComponentRegistrationError):
        registry.register("message", Message)


def test_unknown_component_is_rejected() -> None:
    with pytest.raises(UnknownComponentError):
        ComponentRegistry().factory("missing")


def test_registry_instantiates_component_reference() -> None:
    registry = ComponentRegistry({"message": Message})

    component = registry.instantiate(ComponentRef("message", {"text": "Hello"}))

    assert component == Message("Hello")


def test_factory_must_return_component() -> None:
    def invalid_factory(**props: object) -> Component:
        return "invalid"  # type: ignore[return-value]

    registry = ComponentRegistry({"invalid": invalid_factory})

    with pytest.raises(InvalidRegisteredComponentError):
        registry.instantiate(ComponentRef("invalid"))


def test_registry_rejects_non_callable_factory() -> None:
    with pytest.raises(TypeError, match="must be callable"):
        ComponentRegistry({"message": 42})  # type: ignore[dict-item]
