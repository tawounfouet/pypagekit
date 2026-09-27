"""Symbolic references to explicitly registered components."""

import keyword
import re
from collections.abc import Mapping
from dataclasses import dataclass

from pypagekit.exceptions import InvalidComponentNameError, InvalidComponentPropertyError

from .base import Content

_COMPONENT_NAME_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def validate_component_name(name: str) -> None:
    """Validate a stable public component registry name."""

    if not isinstance(name, str):
        raise TypeError("Component name must be a string.")
    if not _COMPONENT_NAME_RE.fullmatch(name):
        raise InvalidComponentNameError("Component names must use lowercase kebab-case.")


@dataclass(frozen=True, slots=True, init=False)
class ComponentRef(Content):
    """Immutable symbolic reference resolved by an explicit ComponentRegistry."""

    name: str
    props: tuple[tuple[str, object], ...]

    def __init__(
        self,
        name: str,
        props: Mapping[str, object] | None = None,
    ) -> None:
        validate_component_name(name)

        if props is None:
            normalized_props: tuple[tuple[str, object], ...] = ()
        else:
            if not isinstance(props, Mapping):
                raise TypeError("Component reference props must be a mapping or None.")

            entries: list[tuple[str, object]] = []
            for prop_name, value in props.items():
                if not isinstance(prop_name, str):
                    raise TypeError("Component property names must be strings.")
                if not prop_name.isidentifier() or keyword.iskeyword(prop_name):
                    raise InvalidComponentPropertyError(
                        f"Invalid component property name: {prop_name!r}."
                    )
                entries.append((prop_name, value))

            normalized_props = tuple(sorted(entries))

        object.__setattr__(self, "name", name)
        object.__setattr__(self, "props", normalized_props)

    def as_kwargs(self) -> dict[str, object]:
        """Return a fresh keyword-argument mapping for factory invocation."""

        return dict(self.props)
