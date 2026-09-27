# PyPageKit Compatibility, Deprecation, and Migration Policy

This document defines the compatibility rules established by **LOT-35** for the
`0.9.x — API Freeze` line and the future `1.x` stable line.

Machine-readable policy: [`COMPATIBILITY.toml`](COMPATIBILITY.toml)

Active deprecation registry: [`DEPRECATIONS.toml`](DEPRECATIONS.toml)

Public API inventory: [`PUBLIC_API.toml`](PUBLIC_API.toml)

## Compatibility model

PyPageKit applies compatibility guarantees to the public surfaces classified by LOT-34:

```text
stable_candidate
provisional_public
operational_contract
internal
```

Compatibility is evaluated against the **canonical public facade path**, not an implementation
module path.

Covered:

```python
from pypagekit import Page
from pypagekit.build import BuildPlan
from pypagekit.extensions import RendererRegistry
```

Not independently covered:

```python
from pypagekit.domain.page import Page
from pypagekit.build.model import BuildPlan
from pypagekit.extensions.registry import RendererRegistry
```

## Compatible changes

For a stable candidate, the following are normally backward-compatible:

- adding a new public symbol;
- adding a keyword-only optional parameter with a backward-compatible default;
- widening accepted inputs while preserving established behavior;
- adding a more specific exception beneath an already documented public base exception;
- adding a CLI command;
- adding an optional CLI flag without changing existing behavior;
- adding plugin metadata that compatible older consumers may safely ignore;
- improving performance, validation, diagnostics, security, or implementation details without
  changing the established public contract.

Compatible additions still update the public inventory when they create new public surface area.

## Breaking changes

The following are breaking for stable/frozen public contracts:

- removing or renaming a public facade export;
- moving the canonical import path without a compatibility alias;
- removing an accepted argument;
- making an optional argument required;
- changing positional/keyword calling conventions incompatibly;
- narrowing accepted input;
- changing established return semantics incompatibly;
- changing the documented public exception family incompatibly;
- renaming/removing CLI commands or changing process exit-code meaning;
- renaming plugin entry-point groups;
- changing built-in extension IDs;
- changing the extension compatibility line without migration guidance;
- raising the minimum Python version within a stable major without an explicit support-policy
  change.

## The 0.9 freeze line

`0.9.x` is the final contract-shaping period before `1.0.0`.

Stable candidates may still be refined before `0.9.0rc1`, but an incompatible change from the
LOT-34 inventory must be:

1. intentional;
2. recorded in the changelog;
3. reflected in `PUBLIC_API.toml`;
4. covered by migration guidance;
5. represented by a compatibility alias and warning when practical.

LOT-36 will convert the accepted stable candidates into the frozen 1.0 contract.

## Post-1.0 semantic-versioning policy

PyPageKit will use semantic versioning for the frozen public contract.

```text
1.x.y
│ │ └─ patch: compatible fixes
│ └─── minor: compatible additions + deprecations
└───── major: incompatible removals/changes
```

Within a stable major line, an already frozen public API is not silently removed.

A stable API deprecated during `1.x` remains available through the remainder of the `1.x`
major line and may be removed in `2.0.0`.

This is intentionally stronger than a short "two minor releases" policy: application authors may
upgrade within a major without racing a removal clock.

## Deprecation lifecycle

A future public deprecation follows:

```text
ACTIVE
  ↓
document replacement
  ↓
emit DeprecationWarning
  ↓
keep compatibility alias
  ↓
major-version boundary
  ↓
eligible for removal
```

Every deprecation record must include:

```text
id
kind
public_path
since
replacement
removal
```

Example future record:

```toml
[[deprecations]]
id = "example-old-name"
kind = "python"
public_path = "pypagekit.example.OldName"
since = "1.2.0"
replacement = "pypagekit.example.NewName"
removal = "2.0.0"
```

The registry is currently empty because PyPageKit has **no active public deprecations**.

## Warning behavior

Compatibility aliases use the standard Python `DeprecationWarning` category.

A warning message contains:

```text
public path
version where deprecated
replacement
planned removal boundary
```

PyPageKit does not use a custom warning subclass because the standard category already integrates
with Python's warning filters and testing tools.

Applications normally do not display `DeprecationWarning` to end users. Test suites and
development environments should enable them explicitly:

```bash
python -W default::DeprecationWarning -m pytest
```

or:

```python
import warnings

warnings.simplefilter("error", DeprecationWarning)
```

## Migration aliases

When a stable public Python symbol is renamed or moved, PyPageKit should prefer:

```text
old canonical facade path
      ↓
compatibility alias
      ↓ warning
new canonical facade path
```

The old alias must preserve the old behavior closely enough for users to migrate intentionally.

A migration alias is not required for:

- internal/deep-import paths;
- behavior that was never part of the inventoried public contract;
- impossible-to-preserve security flaws;
- invalid behavior whose preservation would contradict the documented contract.

## CLI compatibility

The shell CLI is an operational contract.

Stable CLI compatibility covers:

- command names;
- documented root options;
- argument/option meaning;
- process exit-code meaning.

Current exit semantics:

```text
0  success
1  execution/runtime failure
2  usage/argument validation failure
```

Adding a new command or optional flag is compatible.

Removing/renaming an existing command or changing an existing exit-code meaning is breaking after
the 1.0 freeze.

The Python Typer object under `pypagekit.cli` remains provisional until LOT-36.

## Extension and plugin compatibility

Plugin compatibility is governed by a dedicated extension API identifier:

```text
PYPAGEKIT_EXTENSION_API_VERSION = "0.7"
```

The package version and extension API version are separate:

```text
package release       0.9.0b1
extension API line    0.7
```

A package release may change without changing plugin compatibility.

Changing the extension API line requires:

1. explicit changelog entry;
2. migration guidance;
3. updated plugin examples;
4. lifecycle compatibility behavior;
5. a deliberate decision about whether old plugin lines remain accepted.

LOT-35 does not change the current exact compatibility behavior: a plugin declaring a different
extension API line is rejected during qualification.

## Exception compatibility

Public exception classes are part of the compatibility contract when exported from a stable
facade.

Compatible:

- adding a more specific subclass beneath an existing documented base;
- improving error messages without changing exception type semantics.

Potentially breaking:

- changing a documented public error to an unrelated hierarchy;
- replacing a specific documented error with a generic unrelated error;
- removing a public exception class.

Application code should catch the narrowest stable public base that matches its recovery strategy.

## Typing compatibility

Type annotations on stable public surfaces are part of the compatibility contract.

Potentially breaking typing changes include:

- making an accepted input type narrower;
- making a return type less precise or incompatible;
- removing a protocol member;
- changing a callable protocol incompatibly.

Widening accepted inputs and making return types more precise may be compatible when runtime
behavior remains compatible.

## Security exception

Security fixes may override normal deprecation timing if retaining old behavior would leave users
exposed.

Such a change must still be:

- documented;
- called out in the changelog;
- accompanied by migration guidance when actionable.

Security is not used as a generic exemption from compatibility discipline.

## Current deprecation state

As of `0.9.0b1`:

```text
active public deprecations = 0
```

The purpose of LOT-35 is to establish the mechanism before the first deprecation is needed.

## Relationship to LOT-36

LOT-35 answers:

> How may the public contract evolve?

LOT-36 will answer:

> What exact contract is frozen for 1.0?

At `0.9.0rc1`, the final accepted public inventory, signatures, operational contracts, and
extension contracts will be captured as the 1.0 baseline.
