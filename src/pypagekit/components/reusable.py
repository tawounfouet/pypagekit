"""Built-in reusable components composed from core PyPageKit content."""

from collections.abc import Iterable
from dataclasses import dataclass

from pypagekit.domain import (
    Attributes,
    Component,
    Container,
    Content,
    Heading,
    Link,
    Paragraph,
)
from pypagekit.exceptions import InvalidHeadingLevelError

_EMPTY_ATTRIBUTES = Attributes()


def _normalize_children(
    children: Iterable[Content],
    *,
    component_name: str,
) -> tuple[Content, ...]:
    try:
        normalized = tuple(children)
    except TypeError as exc:
        raise TypeError(
            f"{component_name} children must be an iterable of Content objects."
        ) from exc

    invalid = [child for child in normalized if not isinstance(child, Content)]
    if invalid:
        invalid_type = type(invalid[0]).__name__
        raise TypeError(
            f"{component_name} children must contain only Content objects; got {invalid_type}."
        )

    return normalized


def _validate_heading_level(level: int, *, component_name: str) -> None:
    if not isinstance(level, int) or isinstance(level, bool):
        raise TypeError(f"{component_name} heading level must be an integer from 1 through 6.")
    if not 1 <= level <= 6:
        raise InvalidHeadingLevelError(f"{component_name} heading level must be between 1 and 6.")


def _validate_attributes(value: Attributes, *, field_name: str) -> None:
    if not isinstance(value, Attributes):
        raise TypeError(f"{field_name} must be an Attributes object.")


@dataclass(frozen=True, slots=True, init=False)
class Section(Component):
    """Titled structural section with ordered child content."""

    title: str
    children: tuple[Content, ...]
    heading_level: int
    attributes: Attributes
    heading_attributes: Attributes

    def __init__(
        self,
        title: str,
        children: Iterable[Content] = (),
        *,
        heading_level: int = 2,
        attributes: Attributes = _EMPTY_ATTRIBUTES,
        heading_attributes: Attributes = _EMPTY_ATTRIBUTES,
    ) -> None:
        if not isinstance(title, str):
            raise TypeError("Section title must be a string.")
        _validate_heading_level(heading_level, component_name="Section")
        _validate_attributes(attributes, field_name="Section attributes")
        _validate_attributes(
            heading_attributes,
            field_name="Section heading_attributes",
        )

        object.__setattr__(self, "title", title)
        object.__setattr__(
            self,
            "children",
            _normalize_children(children, component_name="Section"),
        )
        object.__setattr__(self, "heading_level", heading_level)
        object.__setattr__(self, "attributes", attributes)
        object.__setattr__(self, "heading_attributes", heading_attributes)

    def compose(self) -> Content:
        """Compose the section into a heading followed by its children."""

        return Container(
            (
                Heading(
                    self.title,
                    level=self.heading_level,
                    attributes=self.heading_attributes,
                ),
                *self.children,
            ),
            attributes=self.attributes,
        )


@dataclass(frozen=True, slots=True, init=False)
class Card(Component):
    """Optional-titled content card without implicit visual styling."""

    children: tuple[Content, ...]
    title: str | None
    heading_level: int
    attributes: Attributes
    heading_attributes: Attributes

    def __init__(
        self,
        children: Iterable[Content] = (),
        *,
        title: str | None = None,
        heading_level: int = 3,
        attributes: Attributes = _EMPTY_ATTRIBUTES,
        heading_attributes: Attributes = _EMPTY_ATTRIBUTES,
    ) -> None:
        if title is not None and not isinstance(title, str):
            raise TypeError("Card title must be a string or None.")
        _validate_heading_level(heading_level, component_name="Card")
        _validate_attributes(attributes, field_name="Card attributes")
        _validate_attributes(
            heading_attributes,
            field_name="Card heading_attributes",
        )

        object.__setattr__(
            self,
            "children",
            _normalize_children(children, component_name="Card"),
        )
        object.__setattr__(self, "title", title)
        object.__setattr__(self, "heading_level", heading_level)
        object.__setattr__(self, "attributes", attributes)
        object.__setattr__(self, "heading_attributes", heading_attributes)

    def compose(self) -> Content:
        """Compose the card into a neutral container."""

        children: tuple[Content, ...] = self.children
        if self.title is not None:
            children = (
                Heading(
                    self.title,
                    level=self.heading_level,
                    attributes=self.heading_attributes,
                ),
                *children,
            )

        return Container(
            children,
            attributes=self.attributes,
        )


@dataclass(frozen=True, slots=True, init=False)
class Hero(Component):
    """Introductory content block with title, optional body, and optional action."""

    title: str
    body: str | None
    action: Link | None
    heading_level: int
    attributes: Attributes
    heading_attributes: Attributes

    def __init__(
        self,
        title: str,
        *,
        body: str | None = None,
        action: Link | None = None,
        heading_level: int = 1,
        attributes: Attributes = _EMPTY_ATTRIBUTES,
        heading_attributes: Attributes = _EMPTY_ATTRIBUTES,
    ) -> None:
        if not isinstance(title, str):
            raise TypeError("Hero title must be a string.")
        if body is not None and not isinstance(body, str):
            raise TypeError("Hero body must be a string or None.")
        if action is not None and not isinstance(action, Link):
            raise TypeError("Hero action must be a Link or None.")
        _validate_heading_level(heading_level, component_name="Hero")
        _validate_attributes(attributes, field_name="Hero attributes")
        _validate_attributes(
            heading_attributes,
            field_name="Hero heading_attributes",
        )

        object.__setattr__(self, "title", title)
        object.__setattr__(self, "body", body)
        object.__setattr__(self, "action", action)
        object.__setattr__(self, "heading_level", heading_level)
        object.__setattr__(self, "attributes", attributes)
        object.__setattr__(self, "heading_attributes", heading_attributes)

    def compose(self) -> Content:
        """Compose the hero into ordinary core content."""

        children: list[Content] = [
            Heading(
                self.title,
                level=self.heading_level,
                attributes=self.heading_attributes,
            )
        ]
        if self.body is not None:
            children.append(Paragraph(self.body))
        if self.action is not None:
            children.append(self.action)

        return Container(
            children,
            attributes=self.attributes,
        )
