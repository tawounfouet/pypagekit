from dataclasses import dataclass

import pytest

from pypagekit import (
    Content,
    Fragment,
    Layout,
    LayoutRegion,
    Paragraph,
    Slot,
    SlotBindings,
)
from pypagekit.exceptions import MissingRequiredSlotError


@dataclass(frozen=True, slots=True)
class ShellLayout(Layout):
    bindings: SlotBindings

    def regions(self) -> tuple[LayoutRegion, ...]:
        return (
            LayoutRegion(
                "header",
                [Slot("header", [Paragraph("Default header")])],
            ),
            LayoutRegion(
                "main",
                [Slot("main", required=True)],
            ),
        )

    def slot_bindings(self) -> SlotBindings:
        return self.bindings


def test_layout_can_bind_slots_inside_regions() -> None:
    layout = ShellLayout(
        SlotBindings(
            {
                "main": [Paragraph("Body")],
            }
        )
    )

    composed = layout.compose()

    assert composed.children[0] == LayoutRegion(  # type: ignore[attr-defined]
        "header",
        [Fragment([Paragraph("Default header")])],
    )
    assert composed.children[1] == LayoutRegion(  # type: ignore[attr-defined]
        "main",
        [Fragment([Paragraph("Body")])],
    )


def test_layout_required_slot_must_be_bound() -> None:
    with pytest.raises(MissingRequiredSlotError, match="main"):
        ShellLayout(SlotBindings()).compose()


@dataclass(frozen=True, slots=True)
class InvalidLayoutBindings(Layout):
    def regions(self) -> tuple[LayoutRegion, ...]:
        return (LayoutRegion("main"),)

    def slot_bindings(self) -> SlotBindings:
        return {}  # type: ignore[return-value]


def test_layout_rejects_invalid_slot_bindings_type() -> None:
    with pytest.raises(TypeError, match="SlotBindings"):
        InvalidLayoutBindings().compose()
