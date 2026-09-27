"""Named slots and wrapperless content composition."""

import re
from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import final

from pypagekit.exceptions import (
    DuplicateSlotError,
    InvalidSlotBindingError,
    InvalidSlotChildError,
    InvalidSlotNameError,
    MissingRequiredSlotError,
    UnknownSlotBindingError,
)

from .base import Content
from .component import Component

_SLOT_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def _normalize_content(
    values: Iterable[Content],
    *,
    context: str,
) -> tuple[Content, ...]:
    try:
        normalized = tuple(values)
    except TypeError as exc:
        raise TypeError(f"{context} must be an iterable of Content objects.") from exc

    invalid = [value for value in normalized if not isinstance(value, Content)]
    if invalid:
        invalid_type = type(invalid[0]).__name__
        raise InvalidSlotChildError(
            f"{context} must contain only Content objects; got {invalid_type}."
        )

    return normalized


def _validate_slot_name(name: str) -> None:
    if not isinstance(name, str):
        raise TypeError("Slot name must be a string.")
    if not _SLOT_NAME_RE.fullmatch(name):
        raise InvalidSlotNameError("Slot names must use lowercase kebab-case.")


@dataclass(frozen=True, slots=True, init=False)
class Fragment(Content):
    """Ordered content group that introduces no rendering wrapper."""

    children: tuple[Content, ...]

    def __init__(self, children: Iterable[Content] = ()) -> None:
        object.__setattr__(
            self,
            "children",
            _normalize_content(children, context="Fragment children"),
        )


@dataclass(frozen=True, slots=True, init=False)
class Slot(Content):
    """Named placeholder resolved by a slotted composition boundary."""

    name: str
    default: tuple[Content, ...]
    required: bool

    def __init__(
        self,
        name: str,
        default: Iterable[Content] = (),
        *,
        required: bool = False,
    ) -> None:
        _validate_slot_name(name)
        if not isinstance(required, bool):
            raise TypeError("Slot required must be a boolean.")

        normalized_default = _normalize_content(
            default,
            context=f"Slot '{name}' default",
        )
        if required and normalized_default:
            raise InvalidSlotBindingError("Required slots cannot define default content.")

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "default", normalized_default)
        object.__setattr__(self, "required", required)


@dataclass(frozen=True, slots=True, init=False)
class SlotBindings:
    """Immutable mapping from slot names to ordered content groups."""

    entries: tuple[tuple[str, tuple[Content, ...]], ...]

    def __init__(
        self,
        values: Mapping[str, Iterable[Content]] | None = None,
    ) -> None:
        if values is None:
            normalized_entries: tuple[tuple[str, tuple[Content, ...]], ...] = ()
        else:
            if not isinstance(values, Mapping):
                raise TypeError("Slot bindings must be a mapping or None.")

            entries: list[tuple[str, tuple[Content, ...]]] = []
            for name, content in values.items():
                _validate_slot_name(name)
                entries.append(
                    (
                        name,
                        _normalize_content(
                            content,
                            context=f"Slot binding '{name}'",
                        ),
                    )
                )
            normalized_entries = tuple(sorted(entries))

        object.__setattr__(self, "entries", normalized_entries)

    @property
    def names(self) -> tuple[str, ...]:
        """Return bound slot names in deterministic order."""

        return tuple(name for name, _ in self.entries)

    def contains(self, name: str) -> bool:
        """Return whether a slot has an explicit binding."""

        return any(bound_name == name for bound_name, _ in self.entries)

    def get(self, name: str) -> tuple[Content, ...]:
        """Return an explicit binding, raising KeyError when absent."""

        for bound_name, content in self.entries:
            if bound_name == name:
                return content
        raise KeyError(name)


class SlottedComponent(Component, ABC):
    """Component whose template contains named content injection points."""

    __slots__ = ()

    @abstractmethod
    def template(self) -> Content:
        """Return the content template containing zero or more slots."""

    def slot_bindings(self) -> SlotBindings:
        """Return explicit slot bindings for this component."""

        return SlotBindings()

    @final
    def compose(self) -> Content:
        """Resolve the component template against its explicit slot bindings."""

        template = self.template()
        if not isinstance(template, Content):
            raise InvalidSlotBindingError(
                f"{type(self).__name__}.template() must return Content; "
                f"got {type(template).__name__}."
            )

        bindings = self.slot_bindings()
        if not isinstance(bindings, SlotBindings):
            raise InvalidSlotBindingError(
                f"{type(self).__name__}.slot_bindings() must return SlotBindings; "
                f"got {type(bindings).__name__}."
            )

        return bind_slots(template, bindings)


def bind_slots(template: Content, bindings: SlotBindings) -> Content:
    """Resolve every slot in a content template without mutating the source tree."""

    if not isinstance(template, Content):
        raise TypeError("Slot template must be a Content object.")
    if not isinstance(bindings, SlotBindings):
        raise TypeError("Slot bindings must be a SlotBindings object.")

    slot_names = _collect_slot_names(template)
    duplicates = {name for name in slot_names if slot_names.count(name) > 1}
    if duplicates:
        names = ", ".join(sorted(duplicates))
        raise DuplicateSlotError(f"Slot names must be unique within a template; got {names}.")

    unknown = set(bindings.names) - set(slot_names)
    if unknown:
        names = ", ".join(sorted(unknown))
        raise UnknownSlotBindingError(f"Unknown slot bindings: {names}.")

    return _bind_content(template, bindings)


def _collect_slot_names(content: Content) -> tuple[str, ...]:
    from .container import Container
    from .layout import LayoutRegion

    if isinstance(content, Slot):
        return (content.name,)
    if isinstance(content, Fragment | Container | LayoutRegion):
        names: list[str] = []
        for child in content.children:
            names.extend(_collect_slot_names(child))
        return tuple(names)

    return ()


def _bind_content(content: Content, bindings: SlotBindings) -> Content:
    from .container import Container
    from .layout import LayoutRegion

    if isinstance(content, Slot):
        if bindings.contains(content.name):
            return Fragment(bindings.get(content.name))
        if content.required:
            raise MissingRequiredSlotError(
                f"Required slot '{content.name}' has no explicit binding."
            )
        return Fragment(content.default)

    if isinstance(content, Fragment):
        children = _bind_children(content.children, bindings)
        if children is content.children:
            return content
        return Fragment(children)

    if isinstance(content, Container):
        children = _bind_children(content.children, bindings)
        if children is content.children:
            return content
        return Container(children, attributes=content.attributes)

    if isinstance(content, LayoutRegion):
        children = _bind_children(content.children, bindings)
        if children is content.children:
            return content
        return LayoutRegion(
            content.name,
            children,
            attributes=content.attributes,
        )

    return content


def _bind_children(
    children: tuple[Content, ...],
    bindings: SlotBindings,
) -> tuple[Content, ...]:
    resolved = tuple(_bind_content(child, bindings) for child in children)
    if all(
        new is original
        for new, original in zip(
            resolved,
            children,
            strict=True,
        )
    ):
        return children
    return resolved
