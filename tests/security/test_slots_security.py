import pytest

from pypagekit import (
    Link,
    Paragraph,
    Slot,
    SlotBindings,
    SlottedComponent,
)
from pypagekit.exceptions import InvalidSlotNameError, UnsafeUrlError
from pypagekit.rendering import HtmlRenderer


class SecureShell(SlottedComponent):
    def __init__(self, bindings: SlotBindings) -> None:
        self._bindings = bindings

    def template(self) -> Slot:
        return Slot("body", required=True)

    def slot_bindings(self) -> SlotBindings:
        return self._bindings


def test_bound_text_content_still_uses_html_escaping() -> None:
    shell = SecureShell(
        SlotBindings(
            {
                "body": [
                    Paragraph("<script>alert(1)</script>"),
                ]
            }
        )
    )

    html = HtmlRenderer().render(shell)

    assert "<script" not in html.lower()
    assert "&lt;script&gt;" in html


def test_bound_link_still_uses_url_security_policy() -> None:
    shell = SecureShell(
        SlotBindings(
            {
                "body": [
                    Link("Unsafe", "javascript:alert(1)"),
                ]
            }
        )
    )

    with pytest.raises(UnsafeUrlError):
        HtmlRenderer().render(shell)


@pytest.mark.parametrize(
    "name",
    [
        'body" onclick="alert(1)',
        "<script>",
        "body onmouseover",
    ],
)
def test_slot_name_cannot_inject_markup_or_attributes(name: str) -> None:
    with pytest.raises(InvalidSlotNameError):
        Slot(name)


def test_slot_objects_expose_no_raw_html_escape_hatch() -> None:
    slot = Slot("body")

    assert not hasattr(slot, "raw_html")
    assert not hasattr(slot, "safe")
    assert not hasattr(slot, "escape")
