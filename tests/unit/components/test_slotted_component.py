from dataclasses import dataclass

import pytest

from pypagekit import (
    Container,
    Content,
    Fragment,
    Heading,
    Paragraph,
    Slot,
    SlotBindings,
    SlottedComponent,
)
from pypagekit.exceptions import InvalidSlotBindingError


@dataclass(frozen=True, slots=True)
class Shell(SlottedComponent):
    bindings: SlotBindings

    def template(self) -> Content:
        return Container(
            [
                Heading("Shell"),
                Slot("body", required=True),
                Slot(
                    "footer",
                    [Paragraph("Default footer")],
                ),
            ]
        )

    def slot_bindings(self) -> SlotBindings:
        return self.bindings


def test_slotted_component_composes_explicit_bindings_and_defaults() -> None:
    component = Shell(
        SlotBindings(
            {
                "body": [Paragraph("Body")],
            }
        )
    )

    assert component.compose() == Container(
        [
            Heading("Shell"),
            Fragment([Paragraph("Body")]),
            Fragment([Paragraph("Default footer")]),
        ]
    )


def test_slotted_component_can_bind_explicit_empty_content() -> None:
    component = Shell(
        SlotBindings(
            {
                "body": [],
                "footer": [],
            }
        )
    )

    assert component.compose() == Container(
        [
            Heading("Shell"),
            Fragment(),
            Fragment(),
        ]
    )


class InvalidTemplateComponent(SlottedComponent):
    def template(self) -> Content:
        return "invalid"  # type: ignore[return-value]


def test_slotted_component_rejects_invalid_template() -> None:
    with pytest.raises(InvalidSlotBindingError, match="template"):
        InvalidTemplateComponent().compose()


class InvalidBindingsComponent(SlottedComponent):
    def template(self) -> Content:
        return Container()

    def slot_bindings(self) -> SlotBindings:
        return {}  # type: ignore[return-value]


def test_slotted_component_rejects_invalid_bindings_type() -> None:
    with pytest.raises(InvalidSlotBindingError, match="slot_bindings"):
        InvalidBindingsComponent().compose()


def test_slotted_component_has_no_render_method() -> None:
    component = Shell(SlotBindings({"body": [Paragraph("Body")]}))

    assert not hasattr(component, "render")
