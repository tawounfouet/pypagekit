from collections.abc import Callable

import pytest

from pypagekit.rendering.escaping import escape_attribute, escape_text


def test_escape_text_escapes_markup_characters() -> None:
    assert escape_text("A & B < C > D") == "A &amp; B &lt; C &gt; D"


def test_escape_text_does_not_escape_quotes_in_text_context() -> None:
    value = """He said "hello" and it's fine"""

    assert escape_text(value) == value


def test_escape_attribute_escapes_ampersand_markup_and_quotes() -> None:
    value = """A & B < C > D "quoted" 'single'"""

    assert (
        escape_attribute(value)
        == "A &amp; B &lt; C &gt; D &quot;quoted&quot; &#x27;single&#x27;"
    )


def test_escaping_preserves_unicode() -> None:
    value = "Café — 東京 — 你好 — 🔥"

    assert escape_text(value) == value
    assert escape_attribute(value) == value


@pytest.mark.parametrize("function", [escape_text, escape_attribute])
def test_escaping_rejects_non_string_values(
    function: Callable[[str], str],
) -> None:
    with pytest.raises(TypeError):
        function(42)  # type: ignore[arg-type]
