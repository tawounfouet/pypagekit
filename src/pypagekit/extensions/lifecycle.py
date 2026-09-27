"""Explicit immutable plugin lifecycle and conformance."""

from collections import Counter
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum

from pypagekit.exceptions import (
    InvalidPluginLifecycleTransitionError,
    PluginActivationError,
    UnknownPluginError,
)

from .discovery import PluginDiscoveryResult
from .model import (
    PYPAGEKIT_EXTENSION_API_VERSION,
    BuildPlannerExtension,
    ComponentExtension,
    RendererExtension,
    validate_extension_api_version,
)
from .registry import BuildPlannerRegistry, ComponentExtensionRegistry, RendererRegistry


class PluginKind(StrEnum):
    """Stable plugin contribution kinds."""

    BUILD_PLANNER = "build-planner"
    COMPONENT = "component"
    RENDERER = "renderer"


class PluginState(StrEnum):
    """Explicit immutable lifecycle states."""

    DISCOVERED = "discovered"
    QUALIFIED = "qualified"
    REJECTED = "rejected"
    ACTIVE = "active"


@dataclass(frozen=True, slots=True)
class PluginStatus:
    """Lifecycle state for one discovered extension contribution."""

    extension_id: str
    kind: PluginKind
    state: PluginState
    reason: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.extension_id, str) or not self.extension_id:
            raise TypeError("Plugin status extension_id must be a non-empty string.")
        if not isinstance(self.kind, PluginKind):
            raise TypeError("Plugin status kind must be a PluginKind.")
        if not isinstance(self.state, PluginState):
            raise TypeError("Plugin status state must be a PluginState.")
        if self.state is PluginState.REJECTED:
            if not isinstance(self.reason, str) or not self.reason:
                raise TypeError("Rejected plugin status requires a non-empty reason.")
        elif self.reason is not None:
            raise TypeError("Only rejected plugin statuses may carry a reason.")


@dataclass(frozen=True, slots=True)
class PluginLifecycle:
    """Immutable lifecycle over one explicit plugin discovery result."""

    discovery: PluginDiscoveryResult
    statuses: tuple[PluginStatus, ...]
    expected_api_version: str = PYPAGEKIT_EXTENSION_API_VERSION

    def __post_init__(self) -> None:
        if not isinstance(self.discovery, PluginDiscoveryResult):
            raise TypeError("Plugin lifecycle discovery must be a PluginDiscoveryResult.")
        validate_extension_api_version(self.expected_api_version)

        expected = {
            (kind, extension.descriptor.extension_id)
            for kind, extension in _iter_extensions(self.discovery)
        }
        actual: set[tuple[PluginKind, str]] = set()
        for status in self.statuses:
            if not isinstance(status, PluginStatus):
                raise TypeError("Plugin lifecycle statuses must contain PluginStatus objects.")
            key = (status.kind, status.extension_id)
            if key in actual:
                raise TypeError(
                    f"Plugin lifecycle contains duplicate status for '{status.extension_id}' "
                    f"({status.kind.value})."
                )
            actual.add(key)

        if actual != expected:
            raise TypeError("Plugin lifecycle statuses must match discovered extensions exactly.")

        ordered = tuple(sorted(self.statuses, key=_status_sort_key))
        if ordered != self.statuses:
            raise TypeError("Plugin lifecycle statuses must use deterministic ordering.")

    @classmethod
    def from_discovery(
        cls,
        discovery: PluginDiscoveryResult,
        *,
        expected_api_version: str = PYPAGEKIT_EXTENSION_API_VERSION,
    ) -> "PluginLifecycle":
        """Create the discovered state without qualifying or activating plugins."""

        if not isinstance(discovery, PluginDiscoveryResult):
            raise TypeError("Plugin lifecycle discovery must be a PluginDiscoveryResult.")
        validate_extension_api_version(expected_api_version)
        statuses = tuple(
            sorted(
                (
                    PluginStatus(
                        extension.descriptor.extension_id,
                        kind,
                        PluginState.DISCOVERED,
                    )
                    for kind, extension in _iter_extensions(discovery)
                ),
                key=_status_sort_key,
            )
        )
        return cls(discovery, statuses, expected_api_version)

    @property
    def ids(self) -> tuple[str, ...]:
        """Return all discovered plugin IDs in deterministic order."""

        return tuple(status.extension_id for status in self.statuses)

    @property
    def active_ids(self) -> tuple[str, ...]:
        """Return active plugin IDs."""

        return tuple(
            status.extension_id
            for status in self.statuses
            if status.state is PluginState.ACTIVE
        )

    @property
    def rejected_ids(self) -> tuple[str, ...]:
        """Return rejected plugin IDs."""

        return tuple(
            status.extension_id
            for status in self.statuses
            if status.state is PluginState.REJECTED
        )

    @property
    def is_conformant(self) -> bool:
        """Return whether qualification completed without rejected plugins."""

        return bool(self.statuses) and all(
            status.state in {PluginState.QUALIFIED, PluginState.ACTIVE}
            for status in self.statuses
        )

    @property
    def qualified_plugins(self) -> PluginDiscoveryResult:
        """Return registries containing qualified and active contributions."""

        accepted = {
            (status.kind, status.extension_id)
            for status in self.statuses
            if status.state in {PluginState.QUALIFIED, PluginState.ACTIVE}
        }
        return _filter_discovery(self.discovery, accepted)

    @property
    def active_plugins(self) -> PluginDiscoveryResult:
        """Return registries containing only active contributions."""

        accepted = {
            (status.kind, status.extension_id)
            for status in self.statuses
            if status.state is PluginState.ACTIVE
        }
        return _filter_discovery(self.discovery, accepted)

    def status(self, extension_id: str) -> PluginStatus:
        """Return one globally unique plugin status by extension ID."""

        matches = tuple(status for status in self.statuses if status.extension_id == extension_id)
        if not matches:
            raise UnknownPluginError(f"Unknown plugin extension: '{extension_id}'.")
        if len(matches) > 1:
            raise PluginActivationError(
                f"Plugin extension ID '{extension_id}' is ambiguous across contribution kinds."
            )
        return matches[0]

    def qualify(self) -> "PluginLifecycle":
        """Qualify discovered extensions against the current explicit contract."""

        if any(status.state is not PluginState.DISCOVERED for status in self.statuses):
            raise InvalidPluginLifecycleTransitionError(
                "Plugin qualification requires every contribution to be in discovered state."
            )

        id_counts = Counter(status.extension_id for status in self.statuses)
        qualified: list[PluginStatus] = []
        extension_map = {
            (kind, extension.descriptor.extension_id): extension
            for kind, extension in _iter_extensions(self.discovery)
        }

        for status in self.statuses:
            extension = extension_map[(status.kind, status.extension_id)]

            if id_counts[status.extension_id] > 1:
                qualified.append(
                    PluginStatus(
                        status.extension_id,
                        status.kind,
                        PluginState.REJECTED,
                        "extension ID is duplicated across plugin contribution kinds",
                    )
                )
                continue

            api_version = extension.descriptor.api_version
            if api_version is None:
                qualified.append(
                    PluginStatus(
                        status.extension_id,
                        status.kind,
                        PluginState.REJECTED,
                        "extension does not declare a PyPageKit extension API version",
                    )
                )
                continue

            if api_version != self.expected_api_version:
                qualified.append(
                    PluginStatus(
                        status.extension_id,
                        status.kind,
                        PluginState.REJECTED,
                        (
                            f"extension API {api_version} is incompatible with "
                            f"PyPageKit extension API {self.expected_api_version}"
                        ),
                    )
                )
                continue

            failure = _conformance_failure(status.kind, extension)
            if failure is not None:
                qualified.append(
                    PluginStatus(
                        status.extension_id,
                        status.kind,
                        PluginState.REJECTED,
                        failure,
                    )
                )
                continue

            qualified.append(
                PluginStatus(
                    status.extension_id,
                    status.kind,
                    PluginState.QUALIFIED,
                )
            )

        return PluginLifecycle(
            self.discovery,
            tuple(qualified),
            self.expected_api_version,
        )

    def activate(self, extension_ids: Iterable[str] | None = None) -> "PluginLifecycle":
        """Activate qualified plugins explicitly, returning a new lifecycle."""

        self._require_qualified_lifecycle("activation")
        targets = self._activation_targets(extension_ids)
        statuses = tuple(
            PluginStatus(
                status.extension_id,
                status.kind,
                (
                    PluginState.ACTIVE
                    if status.extension_id in targets
                    and status.state in {PluginState.QUALIFIED, PluginState.ACTIVE}
                    else status.state
                ),
                status.reason,
            )
            for status in self.statuses
        )
        return PluginLifecycle(self.discovery, statuses, self.expected_api_version)

    def deactivate(self, extension_ids: Iterable[str] | None = None) -> "PluginLifecycle":
        """Deactivate active plugins explicitly, returning a new lifecycle."""

        self._require_qualified_lifecycle("deactivation")
        if extension_ids is None:
            targets = set(self.active_ids)
        else:
            targets = _normalize_requested_ids(extension_ids)
            known = {status.extension_id: status for status in self.statuses}
            for extension_id in targets:
                status = known.get(extension_id)
                if status is None:
                    raise UnknownPluginError(f"Unknown plugin extension: '{extension_id}'.")
                if status.state is not PluginState.ACTIVE:
                    raise PluginActivationError(
                        f"Plugin extension '{extension_id}' is not active."
                    )

        statuses = tuple(
            PluginStatus(
                status.extension_id,
                status.kind,
                (
                    PluginState.QUALIFIED
                    if status.extension_id in targets and status.state is PluginState.ACTIVE
                    else status.state
                ),
                status.reason,
            )
            for status in self.statuses
        )
        return PluginLifecycle(self.discovery, statuses, self.expected_api_version)

    def _require_qualified_lifecycle(self, operation: str) -> None:
        if any(status.state is PluginState.DISCOVERED for status in self.statuses):
            raise InvalidPluginLifecycleTransitionError(
                f"Plugin {operation} requires qualification first."
            )

    def _activation_targets(self, extension_ids: Iterable[str] | None) -> set[str]:
        if extension_ids is None:
            return {
                status.extension_id
                for status in self.statuses
                if status.state is PluginState.QUALIFIED
            }

        targets = _normalize_requested_ids(extension_ids)
        known = {status.extension_id: status for status in self.statuses}
        for extension_id in targets:
            status = known.get(extension_id)
            if status is None:
                raise UnknownPluginError(f"Unknown plugin extension: '{extension_id}'.")
            if status.state is PluginState.REJECTED:
                raise PluginActivationError(
                    f"Plugin extension '{extension_id}' was rejected during qualification."
                )
            if status.state not in {PluginState.QUALIFIED, PluginState.ACTIVE}:
                raise PluginActivationError(
                    f"Plugin extension '{extension_id}' is not qualified."
                )
        return targets


ExtensionContribution = BuildPlannerExtension | ComponentExtension | RendererExtension


def _iter_extensions(
    discovery: PluginDiscoveryResult,
) -> tuple[tuple[PluginKind, ExtensionContribution], ...]:
    values: list[tuple[PluginKind, ExtensionContribution]] = []
    values.extend((PluginKind.BUILD_PLANNER, item) for item in discovery.build_planners.entries)
    values.extend((PluginKind.COMPONENT, item) for item in discovery.components.entries)
    values.extend((PluginKind.RENDERER, item) for item in discovery.renderers.entries)
    return tuple(values)


def _status_sort_key(status: PluginStatus) -> tuple[str, str]:
    return (status.extension_id, status.kind.value)


def _conformance_failure(
    kind: PluginKind,
    extension: ExtensionContribution,
) -> str | None:
    try:
        if kind is PluginKind.BUILD_PLANNER:
            if not isinstance(extension, BuildPlannerExtension):
                return "build-planner contribution has an invalid extension type"
            BuildPlannerRegistry((extension,)).create(extension.descriptor.extension_id)
        elif kind is PluginKind.COMPONENT:
            if not isinstance(extension, ComponentExtension):
                return "component contribution has an invalid extension type"
            ComponentExtensionRegistry((extension,)).component_registry()
        else:
            if not isinstance(extension, RendererExtension):
                return "renderer contribution has an invalid extension type"
            RendererRegistry((extension,)).create(extension.descriptor.extension_id)
    except Exception as exc:
        return f"{kind.value} conformance failed with {type(exc).__name__}"

    return None


def _filter_discovery(
    discovery: PluginDiscoveryResult,
    accepted: set[tuple[PluginKind, str]],
) -> PluginDiscoveryResult:
    return PluginDiscoveryResult(
        build_planners=BuildPlannerRegistry(
            extension
            for extension in discovery.build_planners.entries
            if (PluginKind.BUILD_PLANNER, extension.descriptor.extension_id) in accepted
        ),
        components=ComponentExtensionRegistry(
            extension
            for extension in discovery.components.entries
            if (PluginKind.COMPONENT, extension.descriptor.extension_id) in accepted
        ),
        renderers=RendererRegistry(
            extension
            for extension in discovery.renderers.entries
            if (PluginKind.RENDERER, extension.descriptor.extension_id) in accepted
        ),
    )


def _normalize_requested_ids(extension_ids: Iterable[str]) -> set[str]:
    values = tuple(extension_ids)
    normalized: set[str] = set()
    for extension_id in values:
        if not isinstance(extension_id, str) or not extension_id:
            raise TypeError("Plugin activation IDs must be non-empty strings.")
        if extension_id in normalized:
            raise PluginActivationError(
                f"Plugin extension '{extension_id}' was requested more than once."
            )
        normalized.add(extension_id)
    return normalized


__all__ = [
    "PluginKind",
    "PluginLifecycle",
    "PluginState",
    "PluginStatus",
]
