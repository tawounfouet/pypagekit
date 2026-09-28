# PyPageKit Public API and Stability Classification

This document defines the public API inventory established by **LOT-34** for the
`0.9.x — API Freeze` release line.

The machine-readable source of truth is [`PUBLIC_API.toml`](PUBLIC_API.toml).
This document explains how to interpret it.

## Purpose

PyPageKit has reached the point where compatibility matters more than adding surface area.

Before `1.0.0`, the project must distinguish:

- APIs intentionally offered to application authors;
- extension contracts intentionally offered to plugin authors;
- operational contracts such as CLI commands and entry-point group names;
- implementation modules that happen to be importable but are not compatibility promises.

LOT-34 created that boundary, LOT-35 defined compatibility rules, and LOT-36 has now frozen the exact 1.0 contract in `API_CONTRACT_1_0.json`.

## Stability classes

### `stable`

A public Python surface covered by PyPageKit's stable-major compatibility contract.

The original `1.0.0` surface is frozen in `API_CONTRACT_1_0.json`. Later `1.x` releases may add
new stable symbols compatibly, but they may not remove or incompatibly mutate that historical floor.

Examples:

```python
from pypagekit import Page, Route, Site
from pypagekit.build import BuildPlan, StaticSiteGenerator
from pypagekit.rendering import HtmlRenderer, Renderer
from pypagekit.extensions import ExtensionDescriptor, RendererRegistry
```

### `provisional_public`

A deliberately public surface that is still allowed to be refined during the 0.9 freeze cycle.

The Python-level Typer adapter is currently the only facade in this class:

```python
from pypagekit.cli import app, main
```

The shell CLI contract is classified separately as an operational contract. Application code
should prefer invoking the installed CLI rather than depending on the concrete Typer application
object.

### `operational_contract`

A user-visible contract that is not primarily a Python import surface.

This includes:

- installed CLI command names and process exit semantics;
- `python -m pypagekit`;
- Python plugin entry-point group names;
- extension compatibility version;
- built-in extension IDs;
- the PEP 561 `py.typed` marker;
- the minimum supported Python version.

### `internal`

Anything not explicitly inventoried as a public facade/export or operational contract.

Internal does **not** mean inaccessible. Python allows deep imports, but importability alone is not
a compatibility promise.

## Canonical import rule

The 1.0 compatibility boundary is attached to the **facade import path**.

Covered:

```python
from pypagekit import Page
from pypagekit.domain import normalize_route_path
from pypagekit.components import ComponentRegistry
from pypagekit.build import BuildPlan
from pypagekit.project import ProjectScaffolder
from pypagekit.extensions import RendererRegistry
from pypagekit.exceptions import UnsafeUrlError
```

Not covered as independent compatibility paths:

```python
from pypagekit.domain.page import Page
from pypagekit.components.registry import ComponentRegistry
from pypagekit.build.model import BuildPlan
from pypagekit.extensions.registry import RendererRegistry
from pypagekit.rendering.security import validate_link_href
```

The second group may continue to work, but PyPageKit reserves the right to reorganize those
implementation modules without treating the reorganization itself as a public API break.

## Frozen stable Python facades

### `pypagekit`

The root package is the author-facing domain convenience facade.

It exports:

```text
Asset
Assets
Attributes
Component
ComponentRef
Container
Content
Fragment
Heading
Image
Layout
LayoutRegion
Link
Navigation
NavigationItem
Node
Page
Paragraph
Route
Site
Sitemap
SitemapEntry
Slot
SlotBindings
SlottedComponent
Text
__version__
bind_slots
```

The root package intentionally does not re-export every PyPageKit subsystem.

### `pypagekit.domain`

The complete public core-domain facade, including semantic base types and domain validators.

In addition to the root conveniences, it exposes:

```text
Action
Media
normalize_route_path
validate_asset_target
```

### `pypagekit.components`

Public component runtime and reusable component surface:

```text
Card
ComponentFactory
ComponentRegistry
ComponentRuntime
Hero
Section
```

### `pypagekit.rendering`

Public representation boundary:

```text
HtmlRenderer
Renderer
```

The `Renderer` protocol is part of the extension and dependency-injection contract.

### `pypagekit.build`

Public static-build boundary:

```text
AssetBuildEntry
BuildFingerprint
BuildManifest
BuildManifestDiff
BuildManifestEntry
BuildPlan
BuildPlanner
BuildPlannerProtocol
FilesystemWriteResult
FilesystemWriter
IncrementalFilesystemWriteResult
IncrementalStaticSiteGenerationResult
PageBuildEntry
StaticSiteGenerationResult
StaticSiteGenerator
build_manifest
diff_build_manifests
route_output_target
```

`BuildPlannerProtocol` is a public structural contract. LOT-39 adds immutable SHA-256 build fingerprints and manifests as compatible `1.1.x` additions. LOT-40 adds deterministic manifest diffs plus drift-safe incremental materialization through `FilesystemWriter.write_incremental()` and `StaticSiteGenerator.generate_incremental()`.

### `pypagekit.project`

Public project-scaffolding application service and its project-specific exceptions.

The entire explicit `pypagekit.project.__all__` surface is a stable API.

### `pypagekit.development`

Public local-development server and explicit filesystem-watch services.

In addition to the existing server configuration/session API, LOT-41 adds:

```text
DevelopmentWatcher
WatchSnapshotEntry
WatchSnapshot
WatchPathKind
WatchChangeKind
WatchChange
WatchChangeBatch
diff_watch_snapshots
DevelopmentWatchError
InvalidWatchRootError
WatchSnapshotError
```

The watcher is polling-based, explicit, and synchronous: constructing it starts no thread and scans
nothing. A snapshot reads regular-file bytes and symlink targets without following symlinks. Empty
directories alone do not create watch entries.

The local server and watcher remain development tools; stability classification does not turn either
into a production runtime claim.

### `pypagekit.diagnostics`

Public read-only project diagnostics and inspection services, result models, statuses, and
diagnostic errors.

### `pypagekit.extensions`

Public plugin and extension contract.

This includes:

- extension descriptors and factories;
- renderer/build-planner/component extension types;
- immutable registries;
- explicit entry-point discovery;
- plugin lifecycle and status types;
- built-in extension IDs;
- entry-point group names;
- compatibility validators;
- default built-in registries.

The extension compatibility line remains:

```text
PYPAGEKIT_EXTENSION_API_VERSION = "0.7"
```

That identifier is deliberately independent from the package version. LOT-36 retains `0.7` for the 1.0 package because no plugin-contract change is required.

### `pypagekit.exceptions`

The explicit package-wide exception facade is a stable API.

For 1.0 compatibility, callers should catch exceptions imported from this facade rather than from
implementation exception modules such as `pypagekit.exceptions.build`.

Project-, development-, and diagnostics-specific exceptions remain public through their respective
subsystem facades.

## CLI contract

The following invocation forms are operational contracts:

```text
pypagekit
python -m pypagekit
```

Current command names:

```text
doctor
inspect
new
serve
```

Root options:

```text
--help
--version
```

Process exit semantics:

```text
0  success
1  framework/runtime execution failure
2  usage/argument validation failure
```

The command names and exit semantics are stability candidates for 1.0.

The Python object `pypagekit.cli.app` is intentionally only `provisional_public`. PyPageKit may
change CLI adapter internals while preserving the shell contract.

## Extension metadata contract

The following entry-point group names are operational contracts:

```text
pypagekit.renderers
pypagekit.build_planners
pypagekit.components
```

Built-in extension IDs:

```text
pypagekit.renderer.html
pypagekit.build.planner
pypagekit.components.builtin
```

These identifiers are externally observable and therefore inventoried separately from Python
implementation modules.

## Typing contract

PyPageKit is a typed package.

The operational typing contract currently includes:

```text
py.typed present
minimum Python = 3.11
mypy strict validation in repository CI
```

Public type aliases, protocols, annotations, and constructor/method signatures of stable
exports are candidates for the 1.0 typing contract.

LOT-36 will freeze the final signature baseline.

## Internal-module policy

Any PyPageKit module not listed as a public facade in `PUBLIC_API.toml` is internal unless a later
compatibility document explicitly promotes it.

Examples include:

```text
pypagekit._filesystem_transaction
pypagekit.build.model
pypagekit.components.registry
pypagekit.domain.route
pypagekit.extensions.registry
pypagekit.rendering.serializer
pypagekit.cli.commands
```

This policy allows implementation refactoring without requiring duplicate compatibility guarantees
for every physical source-file path.

## What LOT-34 freezes and does not freeze

LOT-34 freezes the **inventory and classification process**, not the final 1.0 signatures.

From `0.9.0a1` onward:

1. a new stable facade export must be added to `PUBLIC_API.toml`;
2. removal or demotion of an inventoried surface must be explicit;
3. CLI or extension metadata changes must update the operational inventory;
4. CI verifies that runtime `__all__` values match the inventory;
5. undocumented deep imports remain outside the compatibility promise.

LOT-35 defines those rules in `COMPATIBILITY.md`, `COMPATIBILITY.toml`, and
`MIGRATION_0_9_TO_1_0.md`.

LOT-36 has converted the accepted stable APIs into the final 1.0 contract. The exact baseline is documented in `API_CONTRACT_1_0.md` and stored in `API_CONTRACT_1_0.json`.

## Release-train position

```text
0.9.0a1  LOT-34  inventory + stability classification
    ↓
0.9.0b1  LOT-35  compatibility + deprecation + migration
    ↓
0.9.0rc1 LOT-36  1.0 contract freeze
    ↓
1.0.0    LOT-37  release qualification
```
