import pytest

from pypagekit import Attributes, LayoutRegion, Paragraph
from pypagekit.exceptions import InvalidLayoutRegionNameError
from pypagekit.rendering import HtmlRenderer


@pytest.mark.parametrize(
    "name",
    [
        'main" onclick="alert(1)',
        "<script>",
        "main onmouseover",
    ],
)
def test_layout_region_name_cannot_inject_attributes_or_markup(name: str) -> None:
    with pytest.raises(InvalidLayoutRegionNameError):
        LayoutRegion(name)


def test_layout_region_attribute_values_remain_escaped() -> None:
    region = LayoutRegion(
        "main",
        [Paragraph("Safe")],
        attributes=Attributes(
            title='safe" onclick="alert(1)',
            aria={"label": "<svg onload=alert(1)>"},
        ),
    )

    html = HtmlRenderer().render(region)

    assert ' onclick="' not in html
    assert "<svg" not in html.lower()
    assert "&quot; onclick=&quot;" in html
    assert "&lt;svg onload=alert(1)&gt;" in html
