from collections.abc import Iterable
from dataclasses import FrozenInstanceError, dataclass

import pytest

from pypagekit import (
    Attributes,
    Container,
    Content,
    Layout,
    LayoutRegion,
    Paragraph,
)
from pypagekit.exceptions import (
    DuplicateLayoutRegionError,
    InvalidLayoutRegionChildError,
    InvalidLayoutRegionNameError,
    InvalidLayoutRegionResultError,
)


def test_layout_region_is_content() -> None:
    assert issubclass(LayoutRegion, Content)


def test_layout_is_component_content() -> None:
    assert issubclass(Layout, Content)


def test_layout_region_defaults_to_empty_children_and_attributes() -> None:
    region = LayoutRegion("main")

    assert region.name == "main"
    assert region.children == ()
    assert region.attributes == Attributes()


def test_layout_region_normalizes_children_to_tuple() -> None:
    paragraph = Paragraph("Body")

    region = LayoutRegion("main", [paragraph])

    assert region.children == (paragraph,)


@pytest.mark.parametrize(
    "name",
    ["main", "sidebar", "primary-nav", "footer-2"],
)
def test_layout_region_accepts_lowercase_kebab_names(name: str) -> None:
    assert LayoutRegion(name).name == name


@pytest.mark.parametrize(
    "name",
    ["", "Main", "primary_nav", "-main", "main-", "main--content", "main content"],
)
def test_layout_region_rejects_invalid_names(name: str) -> None:
    with pytest.raises(InvalidLayoutRegionNameError):
        LayoutRegion(name)


def test_layout_region_rejects_non_string_name() -> None:
    with pytest.raises(TypeError, match="name must be a string"):
        LayoutRegion(42)  # type: ignore[arg-type]


def test_layout_region_rejects_non_content_child() -> None:
    with pytest.raises(InvalidLayoutRegionChildError, match="only Content objects"):
        LayoutRegion("main", ["invalid"])  # type: ignore[list-item]


def test_layout_region_rejects_non_iterable_children() -> None:
    with pytest.raises(TypeError, match="iterable of Content"):
        LayoutRegion("main", 42)  # type: ignore[arg-type]


def test_layout_region_accepts_controlled_attributes() -> None:
    attributes = Attributes(id="main", classes=["region"])

    region = LayoutRegion("main", attributes=attributes)

    assert region.attributes is attributes


def test_layout_region_rejects_invalid_attributes_type() -> None:
    with pytest.raises(TypeError, match="Attributes object"):
        LayoutRegion("main", attributes={})  # type: ignore[arg-type]


def test_layout_region_is_immutable() -> None:
    region = LayoutRegion("main")

    with pytest.raises(FrozenInstanceError):
        region.name = "changed"  # type: ignore[misc]


@dataclass(frozen=True, slots=True)
class TwoRegionLayout(Layout):
    def regions(self) -> tuple[LayoutRegion, ...]:
        return (
            LayoutRegion("header", [Paragraph("Header")]),
            LayoutRegion("main", [Paragraph("Body")]),
        )


def test_layout_compose_returns_container_of_regions_in_order() -> None:
    layout = TwoRegionLayout()

    assert layout.compose() == Container(
        [
            LayoutRegion("header", [Paragraph("Header")]),
            LayoutRegion("main", [Paragraph("Body")]),
        ]
    )


class GeneratorLayout(Layout):
    def regions(self) -> Iterable[LayoutRegion]:
        return (
            region
            for region in (
                LayoutRegion("header"),
                LayoutRegion("main"),
            )
        )


def test_layout_accepts_region_generator() -> None:
    composed = GeneratorLayout().compose()

    assert composed == Container(
        [
            LayoutRegion("header"),
            LayoutRegion("main"),
        ]
    )


class DuplicateRegionLayout(Layout):
    def regions(self) -> tuple[LayoutRegion, ...]:
        return (
            LayoutRegion("main"),
            LayoutRegion("main"),
        )


def test_layout_rejects_duplicate_region_names() -> None:
    with pytest.raises(DuplicateLayoutRegionError, match="unique"):
        DuplicateRegionLayout().compose()


class InvalidRegionLayout(Layout):
    def regions(self) -> Iterable[LayoutRegion]:
        return [LayoutRegion("main"), Paragraph("invalid")]  # type: ignore[list-item]


def test_layout_rejects_non_region_results() -> None:
    with pytest.raises(InvalidLayoutRegionResultError, match="LayoutRegion"):
        InvalidRegionLayout().compose()


class NonIterableLayout(Layout):
    def regions(self) -> Iterable[LayoutRegion]:
        return 42  # type: ignore[return-value]


def test_layout_rejects_non_iterable_regions() -> None:
    with pytest.raises(TypeError, match="iterable of LayoutRegion"):
        NonIterableLayout().compose()
