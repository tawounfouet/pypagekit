from dataclasses import dataclass

import pytest

from pypagekit import (
    Component,
    Content,
    Fragment,
    Paragraph,
    Slot,
    SlotBindings,
    SlottedComponent,
)
from pypagekit.components import ComponentRuntime
from pypagekit.exceptions import UnresolvedSlotError


@dataclass(frozen=True, slots=True)
class Message(Component):
    value: str

    def compose(self) -> Content:
        return Paragraph(self.value)


@dataclass(frozen=True, slots=True)
class Host(SlottedComponent):
    bindings: SlotBindings

    def template(self) -> Content:
        return Fragment([Slot("body", required=True)])

    def slot_bindings(self) -> SlotBindings:
        return self.bindings


def test_runtime_resolves_components_in_bound_slot_content() -> None:
    host = Host(
        SlotBindings(
            {
                "body": [Message("Resolved")],
            }
        )
    )

    assert ComponentRuntime().resolve(host) == Fragment(
        [Fragment([Paragraph("Resolved")])]
    )


def test_runtime_preserves_plain_fragment_identity() -> None:
    fragment = Fragment([Paragraph("Body")])

    assert ComponentRuntime().resolve(fragment) is fragment


def test_runtime_recreates_fragment_when_descendant_component_changes() -> None:
    component = Message("Resolved")
    fragment = Fragment([component])

    resolved = ComponentRuntime().resolve(fragment)

    assert resolved is not fragment
    assert resolved == Fragment([Paragraph("Resolved")])
    assert fragment.children == (component,)


def test_runtime_rejects_unresolved_slot() -> None:
    with pytest.raises(UnresolvedSlotError, match="body"):
        ComponentRuntime().resolve(Slot("body"))
