"""Translate controlled domain attributes into HTML serializer values."""

from collections.abc import Mapping

from pypagekit.domain import Attributes

from .serializer import HtmlAttributeValue


def html_attributes(
    attributes: Attributes,
    *,
    intrinsic: Mapping[str, HtmlAttributeValue] | None = None,
) -> dict[str, HtmlAttributeValue]:
    """Build deterministic serializer input from controlled domain attributes."""

    rendered: dict[str, HtmlAttributeValue] = {}

    if attributes.id is not None:
        rendered["id"] = attributes.id
    if attributes.classes:
        rendered["class"] = " ".join(attributes.classes)
    if attributes.title is not None:
        rendered["title"] = attributes.title

    for name, value in attributes.data:
        rendered[f"data-{name}"] = value
    for name, value in attributes.aria:
        rendered[f"aria-{name}"] = value

    if intrinsic is not None:
        rendered.update(intrinsic)

    return rendered
