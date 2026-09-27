from dataclasses import dataclass

import pytest

from pypagekit import (
    Fragment,
    Layout,
    LayoutRegion,
    Link,
    Page,
    Paragraph,
    Slot,
    SlotBindings,
    SlottedComponent,
)
from pypagekit.exceptions import UnresolvedSlotError
from pypagekit.rendering import HtmlRenderer


@dataclass(frozen=True, slots=True)
class Panel(SlottedComponent):
    bindings: SlotBindings

    def template(self) -> Fragment:
        return Fragment(
            [
                Paragraph("Before"),
                Slot("body", required=True),
                Paragraph("After"),
            ]
        )

    def slot_bindings(self) -> SlotBindings:
        return self.bindings


@dataclass(frozen=True, slots=True)
class AppLayout(Layout):
    bindings: SlotBindings

    def regions(self) -> tuple[LayoutRegion, ...]:
        return (
            LayoutRegion(
                "main",
                [Slot("main", required=True)],
            ),
            LayoutRegion(
                "footer",
                [Slot("footer", [Paragraph("Default footer")])],
            ),
        )

    def slot_bindings(self) -> SlotBindings:
        return self.bindings


def test_fragment_renders_without_wrapper_element() -> None:
    fragment = Fragment(
        [
            Paragraph("A"),
            Paragraph("B"),
        ]
    )

    assert HtmlRenderer().render(fragment) == "<p>A</p><p>B</p>"


def test_slotted_component_renders_multiple_bound_nodes_without_extra_wrapper() -> None:
    panel = Panel(
        SlotBindings(
            {
                "body": [
                    Paragraph("One"),
                    Paragraph("Two"),
                ]
            }
        )
    )

    assert HtmlRenderer().render(panel) == (
        "<p>Before</p><p>One</p><p>Two</p><p>After</p>"
    )


def test_explicit_empty_slot_binding_renders_nothing() -> None:
    panel = Panel(SlotBindings({"body": []}))

    assert HtmlRenderer().render(panel) == "<p>Before</p><p>After</p>"


def test_layout_slots_render_inside_their_regions() -> None:
    layout = AppLayout(
        SlotBindings(
            {
                "main": [Paragraph("Body")],
            }
        )
    )

    assert HtmlRenderer().render(layout) == (
        '<div><div data-layout-region="main"><p>Body</p></div>'
        '<div data-layout-region="footer"><p>Default footer</p></div></div>'
    )


def test_slotted_layout_can_be_used_inside_page() -> None:
    page = Page(
        title="Slots",
        content=[
            AppLayout(
                SlotBindings(
                    {
                        "main": [Paragraph("Body")],
                        "footer": [],
                    }
                )
            )
        ],
    )

    html = HtmlRenderer().render(page)

    assert '<div data-layout-region="main"><p>Body</p></div>' in html
    assert '<div data-layout-region="footer"></div>' in html


def test_slot_binding_may_contain_existing_action_content() -> None:
    panel = Panel(
        SlotBindings(
            {
                "body": [Link("Docs", "/docs")],
            }
        )
    )

    assert HtmlRenderer().render(panel) == (
        '<p>Before</p><a href="/docs">Docs</a><p>After</p>'
    )


def test_unresolved_slot_cannot_render_directly() -> None:
    with pytest.raises(UnresolvedSlotError, match="body"):
        HtmlRenderer().render(Slot("body"))


def test_unresolved_slot_inside_page_cannot_render() -> None:
    page = Page(
        title="Invalid",
        content=[Slot("body")],
    )

    with pytest.raises(UnresolvedSlotError, match="body"):
        HtmlRenderer().render(page)
