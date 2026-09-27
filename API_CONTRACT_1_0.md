# PyPageKit 1.0 Contract Freeze

This document records the human-readable decisions behind the **PyPageKit 1.0 public contract**.

The exact machine-readable baseline is:

```text
API_CONTRACT_1_0.json
```

It was generated from `0.9.0rc1` and is enforced by:

```text
tests/architecture/test_1_0_contract_freeze.py
```

The generator is:

```text
tools/api_contract_snapshot.py
```

## Freeze decision

At `0.9.0rc1`, the accepted LOT-34 stable candidates are promoted to **stable**.

Frozen Python facades:

```text
pypagekit
pypagekit.domain
pypagekit.components
pypagekit.rendering
pypagekit.build
pypagekit.project
pypagekit.development
pypagekit.diagnostics
pypagekit.extensions
pypagekit.exceptions
```

The Python/Typer adapter remains explicitly provisional:

```text
pypagekit.cli
```

Its presence is documented, but its `app` / Typer implementation is not part of the frozen 1.0
Python compatibility baseline.

The **shell CLI** is frozen separately as an operational contract.

## What the baseline records

For stable Python facades, the snapshot records:

- exact facade export names;
- function signatures;
- constructor signatures;
- parameter names and parameter kinds;
- public type annotations;
- public return annotations;
- public methods and properties declared by exported classes;
- abstract members;
- public class inheritance relationships;
- public dataclass fields;
- dataclass equality/order/frozen/hash configuration relevant to public semantics;
- public exception hierarchy;
- enum member names and values;
- public type aliases;
- public constant values.

The operational baseline also records:

- installed CLI command name;
- module CLI entry point;
- shell command names;
- root CLI options;
- process exit-code meanings;
- plugin entry-point group names;
- built-in extension IDs;
- extension compatibility API version;
- PEP 561 typing marker;
- minimum supported Python version;
- active public deprecations.

## What the baseline intentionally does not freeze

The contract does **not** freeze physical implementation layout.

Examples outside the contract:

```text
pypagekit.build.model
pypagekit.domain.route
pypagekit.components.registry
pypagekit.extensions.registry
pypagekit.rendering.serializer
pypagekit._filesystem_transaction
pypagekit._deprecation
```

A stable symbol may move between internal modules as long as its canonical facade import and frozen
semantics remain compatible.

Private dataclass fields are excluded from the baseline.

The concrete source module reported by `type.__module__` is not treated as a public compatibility
path.

The actual value of `pypagekit.__version__` is represented as a version symbol rather than frozen
to `0.9.0rc1`, allowing the same contract baseline to qualify `1.0.0`.

## Canonical imports

Covered:

```python
from pypagekit import Page, Route, Site
from pypagekit.build import BuildPlan, StaticSiteGenerator
from pypagekit.components import ComponentRegistry
from pypagekit.extensions import RendererRegistry
from pypagekit.exceptions import BuildError
from pypagekit.rendering import HtmlRenderer, Renderer
```

Not independently covered:

```python
from pypagekit.build.model import BuildPlan
from pypagekit.components.registry import ComponentRegistry
from pypagekit.extensions.registry import RendererRegistry
```

## CLI freeze

Frozen invocation forms:

```text
pypagekit
python -m pypagekit
```

Frozen commands:

```text
doctor
inspect
new
serve
```

Frozen root options:

```text
--help
--version
```

Frozen process exit semantics:

```text
0  success
1  framework/runtime execution failure
2  usage/argument validation failure
```

The shell contract is stable even though the underlying Python Typer object remains provisional.

## Extension contract freeze

The 1.0 package intentionally retains the existing extension compatibility line:

```text
PYPAGEKIT_EXTENSION_API_VERSION = "0.7"
```

This is not an error or a version mismatch. Package version and extension-contract version are
independent compatibility dimensions.

Frozen entry-point groups:

```text
pypagekit.renderers
pypagekit.build_planners
pypagekit.components
```

Frozen built-in extension IDs:

```text
pypagekit.renderer.html
pypagekit.build.planner
pypagekit.components.builtin
```

No plugin migration is required between `0.9.0b1`, `0.9.0rc1`, and `1.0.0`.

## Python and typing freeze

Minimum supported Python:

```text
3.11
```

Release qualification matrix:

```text
3.11
3.12
3.13
3.14
```

The package remains PEP 561 typed through `py.typed`.

Public annotations and protocol members included in the JSON baseline are part of the frozen
contract.

## Cross-version normalization

The snapshot generator normalizes runtime-only standard-library implementation differences that do
not represent PyPageKit API differences.

For example, Python 3.13 may expose pathlib runtime classes through:

```text
pathlib._local.Path
```

while other supported runtimes expose:

```text
pathlib.Path
```

The contract normalizes both to the public standard-library name `pathlib.Path`.

The resulting baseline has been proven identical on Python 3.11, 3.12, 3.13, and 3.14.

## Deprecation state at freeze

At `0.9.0rc1`:

```text
active public deprecations = 0
```

No compatibility alias is required for the 1.0 release.

## Freeze gate

During the RC-to-1.0 interval:

```text
runtime public surface
        ↓
contract snapshot generator
        ↓
canonical JSON
        ↓ exact comparison
API_CONTRACT_1_0.json
        ↓
pass / fail
```

Any drift fails CI.

A necessary contract change after this freeze requires an explicit decision, updated migration
guidance, changelog documentation, a refreshed release candidate, and a new reviewed baseline. It
must never happen silently.

## Relationship to post-1.0 evolution

`API_CONTRACT_1_0.json` is the historical baseline for the 1.0 contract.

The compatibility policy in `COMPATIBILITY.md` governs future evolution:

- compatible additions may appear in later minor releases;
- deprecations remain available through the current major line;
- incompatible removals wait for the next major release.

LOT-36 freezes **what 1.0 starts with**. It does not prohibit compatible evolution of later 1.x
releases.

## Release-train position

```text
0.9.0a1  inventory
    ↓
0.9.0b1  compatibility policy
    ↓
0.9.0rc1 exact 1.0 contract freeze
    ↓
1.0.0    release qualification
```

LOT-37 may change the package release version and release metadata, but must not change the frozen
1.0 contract.
