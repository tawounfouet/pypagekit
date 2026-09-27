"""Runtime resolution for PyPageKit components."""

from pypagekit.domain import (
    Component,
    Container,
    Content,
    Fragment,
    LayoutRegion,
    Slot,
)
from pypagekit.exceptions import (
    ComponentCycleError,
    ComponentResolutionDepthError,
    InvalidComponentResultError,
    UnresolvedSlotError,
)


class ComponentRuntime:
    """Resolve components into ordinary content trees before rendering."""

    def __init__(self, *, max_depth: int = 100) -> None:
        if not isinstance(max_depth, int) or isinstance(max_depth, bool):
            raise TypeError("Component runtime max_depth must be an integer.")
        if max_depth < 1:
            raise ValueError("Component runtime max_depth must be at least 1.")

        self._max_depth = max_depth

    @property
    def max_depth(self) -> int:
        """Maximum number of nested component compositions."""

        return self._max_depth

    def resolve(self, content: Content) -> Content:
        """Resolve every component reachable from a content node."""

        if not isinstance(content, Content):
            raise TypeError("Component runtime can resolve only Content objects.")

        return self._resolve(
            content,
            active_component_ids=set(),
            component_depth=0,
        )

    def _resolve(
        self,
        content: Content,
        *,
        active_component_ids: set[int],
        component_depth: int,
    ) -> Content:
        if isinstance(content, Component):
            return self._resolve_component(
                content,
                active_component_ids=active_component_ids,
                component_depth=component_depth,
            )

        if isinstance(content, Slot):
            raise UnresolvedSlotError(
                f"Slot '{content.name}' reached the component runtime unresolved."
            )

        if isinstance(content, Fragment):
            resolved_children = self._resolve_children(
                content.children,
                active_component_ids=active_component_ids,
                component_depth=component_depth,
            )
            if resolved_children is content.children:
                return content
            return Fragment(resolved_children)

        if isinstance(content, Container):
            resolved_children = self._resolve_children(
                content.children,
                active_component_ids=active_component_ids,
                component_depth=component_depth,
            )
            if resolved_children is content.children:
                return content

            return Container(
                resolved_children,
                attributes=content.attributes,
            )

        if isinstance(content, LayoutRegion):
            resolved_children = self._resolve_children(
                content.children,
                active_component_ids=active_component_ids,
                component_depth=component_depth,
            )
            if resolved_children is content.children:
                return content

            return LayoutRegion(
                content.name,
                resolved_children,
                attributes=content.attributes,
            )

        return content

    def _resolve_children(
        self,
        children: tuple[Content, ...],
        *,
        active_component_ids: set[int],
        component_depth: int,
    ) -> tuple[Content, ...]:
        resolved_children = tuple(
            self._resolve(
                child,
                active_component_ids=active_component_ids,
                component_depth=component_depth,
            )
            for child in children
        )

        if all(
            resolved is original
            for resolved, original in zip(
                resolved_children,
                children,
                strict=True,
            )
        ):
            return children

        return resolved_children

    def _resolve_component(
        self,
        component: Component,
        *,
        active_component_ids: set[int],
        component_depth: int,
    ) -> Content:
        if component_depth >= self._max_depth:
            raise ComponentResolutionDepthError(
                f"Component resolution exceeded max_depth={self._max_depth}."
            )

        identity = id(component)
        if identity in active_component_ids:
            raise ComponentCycleError(f"Component cycle detected at {type(component).__name__}.")

        active_component_ids.add(identity)
        try:
            composed = component.compose()
            if not isinstance(composed, Content):
                raise InvalidComponentResultError(
                    f"{type(component).__name__}.compose() must return Content; "
                    f"got {type(composed).__name__}."
                )

            return self._resolve(
                composed,
                active_component_ids=active_component_ids,
                component_depth=component_depth + 1,
            )
        finally:
            active_component_ids.remove(identity)
