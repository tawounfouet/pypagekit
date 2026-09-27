from dataclasses import FrozenInstanceError

import pytest

from pypagekit import (
    Container,
    Fragment,
    LayoutRegion,
    Paragraph,
    Slot,
    SlotBindings,
    bind_slots,
)
from pypagekit.exceptions import (
    DuplicateSlotError,
    InvalidSlotBindingError,
    InvalidSlotChildError,
    InvalidSlotNameError,
    MissingRequiredSlotError,
    UnknownSlotBindingError,
)


def test_fragment_normalizes_children_to_tuple() -> None:
    paragraph = Paragraph("Body")
    fragment = Fragment([paragraph])

    assert fragment.children == (paragraph,)


def test_fragment_accepts_empty_content() -> None:
    assert Fragment().children == ()


def test_fragment_rejects_non_content_children() -> None:
    with pytest.raises(InvalidSlotChildError, match="only Content"):
        Fragment(["invalid"])  # type: ignore[list-item]


def test_fragment_is_immutable() -> None:
    fragment = Fragment([Paragraph("Body")])

    with pytest.raises(FrozenInstanceError):
        fragment.children = ()  # type: ignore[misc]


@pytest.mark.parametrize(
    "name",
    ["body", "primary", "side-bar", "footer-2"],
)
def test_slot_accepts_lowercase_kebab_case_names(name: str) -> None:
    assert Slot(name).name == name


@pytest.mark.parametrize(
    "name",
    ["", "Body", "side_bar", "-body", "body-", "body--main", "body main"],
)
def test_slot_rejects_invalid_names(name: str) -> None:
    with pytest.raises(InvalidSlotNameError):
        Slot(name)


def test_slot_rejects_non_string_name() -> None:
    with pytest.raises(TypeError, match="name must be a string"):
        Slot(42)  # type: ignore[arg-type]


def test_slot_default_normalizes_to_tuple() -> None:
    paragraph = Paragraph("Fallback")
    slot = Slot("body", [paragraph])

    assert slot.default == (paragraph,)


def test_required_slot_cannot_define_default_content() -> None:
    with pytest.raises(InvalidSlotBindingError, match="cannot define default"):
        Slot(
            "body",
            [Paragraph("Fallback")],
            required=True,
        )


def test_slot_required_must_be_boolean() -> None:
    with pytest.raises(TypeError, match="must be a boolean"):
        Slot("body", required=1)  # type: ignore[arg-type]


def test_slot_bindings_are_sorted_deterministically() -> None:
    bindings = SlotBindings(
        {
            "zeta": [Paragraph("Z")],
            "alpha": [Paragraph("A")],
        }
    )

    assert bindings.names == ("alpha", "zeta")
    assert bindings.get("alpha") == (Paragraph("A"),)
    assert bindings.get("zeta") == (Paragraph("Z"),)


def test_slot_bindings_distinguish_absent_from_explicit_empty() -> None:
    bindings = SlotBindings({"body": []})

    assert bindings.contains("body")
    assert bindings.get("body") == ()
    assert not bindings.contains("footer")


def test_slot_bindings_get_raises_for_absent_name() -> None:
    with pytest.raises(KeyError):
        SlotBindings().get("missing")


def test_slot_bindings_reject_non_mapping_input() -> None:
    with pytest.raises(TypeError, match="mapping or None"):
        SlotBindings([("body", [])])  # type: ignore[arg-type]


def test_slot_bindings_reject_non_content_values() -> None:
    with pytest.raises(InvalidSlotChildError):
        SlotBindings({"body": ["invalid"]})  # type: ignore[list-item]


def test_bind_slots_replaces_slot_with_fragment() -> None:
    template = Container([Slot("body", required=True)])
    bindings = SlotBindings(
        {
            "body": [
                Paragraph("A"),
                Paragraph("B"),
            ]
        }
    )

    assert bind_slots(template, bindings) == Container(
        [
            Fragment(
                [
                    Paragraph("A"),
                    Paragraph("B"),
                ]
            )
        ]
    )


def test_bind_slots_uses_default_when_binding_is_absent() -> None:
    template = Container(
        [
            Slot(
                "footer",
                [Paragraph("Fallback")],
            )
        ]
    )

    assert bind_slots(template, SlotBindings()) == Container([Fragment([Paragraph("Fallback")])])


def test_explicit_empty_binding_suppresses_default() -> None:
    template = Container(
        [
            Slot(
                "footer",
                [Paragraph("Fallback")],
            )
        ]
    )

    assert bind_slots(
        template,
        SlotBindings({"footer": []}),
    ) == Container([Fragment()])


def test_required_slot_must_have_explicit_binding() -> None:
    template = Container([Slot("body", required=True)])

    with pytest.raises(MissingRequiredSlotError, match="body"):
        bind_slots(template, SlotBindings())


def test_unknown_binding_is_rejected() -> None:
    template = Container([Slot("body")])

    with pytest.raises(UnknownSlotBindingError, match="unknown"):
        bind_slots(
            template,
            SlotBindings({"unknown": [Paragraph("No")]}),
        )


def test_duplicate_slot_names_are_rejected_even_when_nested() -> None:
    template = Container(
        [
            Slot("body"),
            LayoutRegion(
                "main",
                [Slot("body")],
            ),
        ]
    )

    with pytest.raises(DuplicateSlotError, match="body"):
        bind_slots(template, SlotBindings())


def test_bind_slots_resolves_slots_inside_layout_regions() -> None:
    template = LayoutRegion(
        "main",
        [Slot("body")],
    )

    result = bind_slots(
        template,
        SlotBindings({"body": [Paragraph("Body")]}),
    )

    assert result == LayoutRegion(
        "main",
        [Fragment([Paragraph("Body")])],
    )


def test_bind_slots_preserves_source_tree() -> None:
    slot = Slot("body")
    template = Container([slot])

    result = bind_slots(
        template,
        SlotBindings({"body": [Paragraph("Resolved")]}),
    )

    assert template.children == (slot,)
    assert result is not template


def test_bind_slots_preserves_identity_when_template_has_no_slots() -> None:
    template = Container([Paragraph("Body")])

    assert bind_slots(template, SlotBindings()) is template
