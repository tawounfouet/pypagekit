# PyPageKit 1.x Roadmap

This roadmap opens the first compatible minor evolution after the qualified `1.0.0` baseline.

The historical LOT-01 → LOT-37 train remains closed. The frozen 1.0 contract in
`API_CONTRACT_1_0.json` remains immutable and acts as the compatibility floor for the complete 1.x
major line.

## 1.1.x theme — Incremental Developer Experience

The first post-1.0 line turns capabilities that were explicitly deferred before 1.0 into a coherent
developer workflow:

```text
frozen 1.0 baseline
        ↓
compatible 1.x evolution gate
        ↓
artifact fingerprints + manifest
        ↓
incremental build diff
        ↓
filesystem watch service
        ↓
serve --watch + live reload
        ↓
1.1 release candidate
        ↓
1.1.0
```

## LOT sequence

| LOT | Scope | Target |
|---|---|---|
| LOT-38 | Post-1.0 Compatibility Baseline Gate | `1.1.0a1` |
| LOT-39 | Build Fingerprints & Manifest | `1.1.0a2` |
| LOT-40 | Incremental Build Diff & Materialization | `1.1.0a3` |
| LOT-41 | Watch Service & Change Detection | `1.1.0b1` |
| LOT-42 | Serve Watch Mode & Live Reload | `1.1.0b2` |
| LOT-43 | 1.1 Public Contract Snapshot & Release Candidate | `1.1.0rc1` |
| LOT-44 | 1.1 Release Qualification | `1.1.0` |

## Current position

```text
LOT-38  1.1.0a1  compatibility baseline gate   ✅ qualified
LOT-39  1.1.0a2  build fingerprints + manifest ✅ qualified
LOT-40  1.1.0a3  incremental build diff         ✅ qualified
LOT-41  1.1.0b1  watch service + change detection ✅ qualified
LOT-42  1.1.0b2  serve --watch + live reload     ✅ qualified
LOT-43  1.1.0rc1  1.1 public contract snapshot   ✅ qualified
LOT-44  1.1.0     release qualification           ← next
```

## LOT-38 — Post-1.0 Compatibility Baseline Gate

LOT-36 used exact runtime equality during the `0.9.0rc1 → 1.0.0` freeze interval. That rule cannot
remain the long-term 1.x gate because semantic versioning explicitly permits compatible additions in
minor releases.

LOT-38 changes the question from:

```text
current runtime == 1.0 baseline
```

to:

```text
current runtime >= compatible 1.0 baseline
```

The 1.0 JSON file remains byte-for-byte frozen.

The comparator permits compatible evolution such as:

- new public facade exports;
- new class/protocol members;
- new optional keyword-only parameters with backward-compatible defaults;
- new CLI commands;
- new root CLI options.

It rejects, at minimum:

- removal of a frozen export;
- incompatible changes to existing parameter names, kinds, annotations, defaults, or ordering;
- incompatible return annotation changes;
- removal or incompatible mutation of frozen public members;
- incompatible class base/dataclass changes;
- CLI command/option removal;
- CLI exit-code meaning changes;
- extension API line changes;
- frozen plugin identity/group changes;
- minimum-Python changes inside the stable major.

The comparator is deliberately conservative. A change that is semantically compatible but cannot be
proven safely from the machine-readable contract should require an explicit reviewed evolution of the
compatibility checker rather than silently passing.

## LOT-39 — Build Fingerprints & Manifest

Introduce immutable deterministic primitives for describing the identity of generated artifacts
without changing filesystem output behavior.

Planned concepts:

```text
BuildFingerprint
BuildManifestEntry
BuildManifest
```

The implementation is explicit and deterministic:

```text
PageBuildEntry.content
        ↓ UTF-8 bytes
    SHA-256
        ↓
BuildFingerprint

Asset.source
        ↓ explicit streamed read
    SHA-256
        ↓
BuildFingerprint
```

`BuildManifest` preserves BuildPlan declaration order while maintaining a private immutable sorted
lookup index. Asset source state is compared before and after hashing so a concurrent mutation fails
explicitly rather than yielding a mixed-content fingerprint.

The lot introduces no output writes, background watchers, hidden build execution, or persistent
cache files.

## LOT-40 — Incremental Build Diff & Materialization

Use two manifests to classify build output:

```text
previous manifest
       +
next manifest
       ↓
unchanged
changed
added
removed
       ↓
minimal materialization plan
```

The implementation also verifies the actual previous output before mutating it:

```text
previous BuildManifest
       +
current files under output_root
       ↓
fingerprint verification
       │
       ├── drift → fail closed
       └── intact
             +
        next BuildManifest
             ↓
       one transaction
```

Only added/changed targets are written. Removed targets are backed up transactionally before deletion,
so a later failure restores them together with changed files and removes newly added files.
Unchanged targets are not rewritten, and unplanned output files remain untouched.

Existing rollback, symlink, hard-link, collision, and filesystem safety guarantees remain mandatory.
LOT-40 deliberately leaves empty-directory pruning out of scope.

## LOT-41 — Watch Service & Change Detection

Add an explicit development watch service.

The watch layer remains separate from the HTTP server:

```text
filesystem
   ↓ explicit snapshot
WatchSnapshot
   ↓ polling comparison
WatchChangeBatch
   ├── created
   ├── modified
   └── deleted
   ↓
application-owned decision
```

The implementation uses standard-library polling rather than a third-party watcher dependency.
Regular files are SHA-256 content fingerprinted. Symlinks are recorded by link-target identity and
never followed. Relative ignore prefixes allow callers to exclude output trees such as `dist/`.

`wait_for_changes()` is synchronous and explicitly blocking. It polls until a first change is
observed, then continues until no further snapshot change occurs during the configured debounce
window, returning one deterministic batch against the original snapshot.

No import-time watcher, background global thread, callback executor, implicit project execution, or
HTTP-server integration is introduced.

## LOT-42 — Serve Watch Mode & Live Reload

Integrate the explicit watch/build path with the local development server.

Operational surface:

```bash
pypagekit serve --watch
```

The established `pypagekit serve` path remains unchanged by default.

Watch mode uses a fresh Python subprocess to load the project entry and obtain a deterministic
`BuildPlan`, then delegates filesystem mutation to LOT-40:

```text
source change
    ↓
DevelopmentWatcher
    ↓
fresh subprocess
    ↓
BuildPlan
    ↓
FilesystemWriter.write_incremental()
    ↓
successful transaction commit
    ↓
notify_reload()
```

The subprocess contract requires module-level `site` and optionally accepts module-level `assets`.
The generated output tree is excluded from source watching to prevent rebuild loops.

Live reload is implemented by the development server only when explicitly enabled. HTML files are
not modified on disk: the server injects one external same-origin script into HTML responses, while
an internal no-store revision endpoint signals successful rebuilds. The existing self-only CSP remains
in force without `unsafe-inline`.

A failed project import, render, or incremental write leaves the last successful output online and
does not advance the browser reload revision.

## LOT-43 — 1.1 Public Contract Snapshot & Release Candidate

Inventory all compatible public additions introduced by LOT-39 through LOT-42 and create a canonical
1.1 snapshot.

The 1.0 contract remains the compatibility floor:

```text
API_CONTRACT_1_0.json   immutable historical floor
API_CONTRACT_1_1.json   exact 1.1 release snapshot
```

The release-candidate gate is intentionally dual:

```text
API_CONTRACT_1_0.json
        ↓ compatible-superset comparator
API_CONTRACT_1_1.json
        ↓ exact runtime equality
1.1.0rc1 runtime
```

The 1.1 snapshot captures the additive build-manifest, incremental materialization, filesystem-watch,
live-reload, and `serve --watch` surfaces. Command arguments/options are now part of the
machine-readable operational CLI inventory.

The Python/Typer facade remains provisional, extension API compatibility remains `0.7`, minimum
Python remains 3.11, and active public deprecations remain empty.

Target: `1.1.0rc1`.

## LOT-44 — 1.1 Release Qualification

Final qualification mirrors the 1.0 discipline:

- Python 3.11 / 3.12 / 3.13 / 3.14;
- Ruff;
- mypy;
- pytest;
- sdist + wheel;
- clean installation;
- installed CLI;
- generated-project smoke;
- 1.0 backward-compatibility gate;
- exact 1.1 RC contract gate.

Target: `1.1.0`.

## Explicitly outside 1.1.x

The following capabilities were also deferred before 1.0 but are not bundled into the first minor
line:

- parallel page rendering;
- worker pools;
- asynchronous filesystem materialization;
- cross-process build caches;
- filesystem journaling or crash-safe multi-process transactions;
- automatic retry/background recovery supervisors;
- production HTTP serving;
- TLS termination;
- browser auto-open;
- arbitrary raw-HTML trust bypasses.

These require separate product and trust-boundary decisions and should not be smuggled into the
incremental developer-experience line.

## Compatibility rule

Every LOT in 1.1.x must satisfy both:

```text
current public inventory
        ↓
new 1.1 additions
```

and:

```text
frozen 1.0 baseline
        ↓ compatibility comparator
current runtime
        ↓
PASS
```

A 1.1 feature is not complete merely because its own tests pass. It must also preserve the complete
1.0 compatibility floor.
