"""Explicit immutable registry for symbolic component lookup."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass, field

from pypagekit.domain import Component, ComponentRef
from pypagekit.domain.reference import validate_component_name
from pypagekit.exceptions import (
    DuplicateComponentRegistrationError,
    InvalidRegisteredComponentError,
    UnknownComponentError,
)

ComponentFactory = Callable[..., Component]


@dataclass(frozen=True, slots=True, init=False)
class ComponentRegistry:
    """Immutable mapping from stable names to component factories."""

    entries: tuple[tuple[str, ComponentFactory], ...]
    _names: tuple[str, ...] = field(repr=False, compare=False)

    def __init__(
        self,
        values: Mapping[str, ComponentFactory] | None = None,
    ) -> None:
        if values is None:
            normalized_entries: tuple[tuple[str, ComponentFactory], ...] = ()
        else:
            if not isinstance(values, Mapping):
                raise TypeError("Component registry values must be a mapping or None.")

            entries: list[tuple[str, ComponentFactory]] = []
            for name, factory in values.items():
                validate_component_name(name)
                if not callable(factory):
                    raise TypeError(f"Component factory for '{name}' must be callable.")
                entries.append((name, factory))

            normalized_entries = tuple(sorted(entries, key=lambda item: item[0]))

        object.__setattr__(self, "entries", normalized_entries)
        object.__setattr__(self, "_names", tuple(name for name, _ in normalized_entries))

    @property
    def names(self) -> tuple[str, ...]:
        """Return registered names in deterministic order."""

        return self._names

    def contains(self, name: str) -> bool:
        """Return whether a component name is registered."""

        validate_component_name(name)
        return _component_index(self._names, name) is not None

    def register(
        self,
        name: str,
        factory: ComponentFactory,
    ) -> "ComponentRegistry":
        """Return a new registry containing one additional registration."""

        validate_component_name(name)
        if not callable(factory):
            raise TypeError(f"Component factory for '{name}' must be callable.")
        if self.contains(name):
            raise DuplicateComponentRegistrationError(f"Component '{name}' is already registered.")

        values = dict(self.entries)
        values[name] = factory
        return ComponentRegistry(values)

    def factory(self, name: str) -> ComponentFactory:
        """Return the factory registered under a stable name."""

        validate_component_name(name)
        index = _component_index(self._names, name)
        if index is not None:
            return self.entries[index][1]
        raise UnknownComponentError(f"Unknown component: '{name}'.")

    def instantiate(self, reference: ComponentRef) -> Component:
        """Instantiate a registered component from an immutable reference."""

        if not isinstance(reference, ComponentRef):
            raise TypeError("Component registry can instantiate only ComponentRef objects.")

        factory = self.factory(reference.name)
        component = factory(**reference.as_kwargs())
        if not isinstance(component, Component):
            raise InvalidRegisteredComponentError(
                f"Factory for '{reference.name}' must return Component; "
                f"got {type(component).__name__}."
            )

        return component


def _component_index(names: tuple[str, ...], name: str) -> int | None:
    low = 0
    high = len(names)
    while low < high:
        middle = (low + high) // 2
        candidate = names[middle]
        if candidate < name:
            low = middle + 1
        elif candidate > name:
            high = middle
        else:
            return middle
    return None
