# Changelog

All notable changes to PyPageKit will be documented in this file.

## [Unreleased]

## [1.1.0rc1]

### Contract freeze

- Add canonical machine-readable `API_CONTRACT_1_1.json` generated from the release-candidate runtime.
- Add human-readable `API_CONTRACT_1_1.md`.
- Preserve `API_CONTRACT_1_0.json` as the immutable historical compatibility floor.
- Add exact runtime-to-`API_CONTRACT_1_1.json` architecture gating across the supported Python matrix.
- Require the frozen 1.1 snapshot itself to remain a compatible superset of the 1.0 baseline.
- Record the dedicated `release_1_1_freeze` policy in `COMPATIBILITY.toml`.
- Expand machine-readable CLI inventory with command arguments and explicit command options, including `serve --watch`.
- Keep the Python/Typer `pypagekit.cli` facade provisional.
- Keep extension compatibility API `0.7` unchanged.
- Confirm zero active public deprecations at the 1.1 freeze.

### Release

- Advance the development version to `1.1.0rc1`.
- LOT-44 may qualify `1.1.0` but must not silently change the frozen 1.1 contract.

## [1.1.0b2]

### Added

- Opt-in `pypagekit serve --watch` development workflow.
- Fresh-process project-plan loading for watch rebuilds, avoiding stale imported local modules.
- Automatic initial build before starting the watched development server.
- Incremental rebuilds through the qualified LOT-40 filesystem transition.
- Browser live reload through same-origin development-server resources.
- Public optional `DevelopmentServer.create(..., live_reload=True)` mode.
- Public `DevelopmentServerSession.live_reload` state and `notify_reload()` revision signal.
- Watch tuning options `--entry`, `--poll-interval`, and `--debounce-interval`.

### Watch + rebuild semantics

- `serve` without `--watch` preserves its existing behavior.
- Watch mode requires the selected entry file to remain inside the current project root and not traverse symlinks.
- The project entry executes in a fresh Python subprocess with `PYTHONDONTWRITEBYTECODE=1`.
- The entry must expose module-level `site`; optional module-level `assets` is supported.
- Project stdout is redirected away from the machine-readable plan payload.
- The initial build completes before the HTTP server binds.
- The generated output tree and common local cache/environment directories are excluded from source watching.
- Rebuild failures keep the last successful output and do not advance the browser reload revision.
- Successful rebuilds use `FilesystemWriter.write_incremental()` and notify browsers only after commit.

### Live reload semantics

- Live reload is disabled by default.
- HTML files on disk are never modified to add reload code.
- In live-reload mode, HTML responses receive one external same-origin script tag dynamically.
- The script polls an internal revision endpoint and reloads only after the revision changes.
- No inline script permission is added; the existing self-only CSP remains in force.
- Binary responses remain byte-for-byte unchanged.
- Symlink/traversal protections continue to apply to the live-reload HTML path.
- The internal live-reload resource paths are reserved only while live-reload mode is enabled.

### Release

- Advance the development version to `1.1.0b2`.

## [1.1.0b1]

### Added

- Public synchronous `DevelopmentWatcher` with explicit `snapshot()`, `poll()`, and `wait_for_changes()` operations.
- Immutable `WatchSnapshotEntry`, `WatchSnapshot`, `WatchChange`, and `WatchChangeBatch` models.
- Public `WatchPathKind` and `WatchChangeKind` enums.
- Public pure `diff_watch_snapshots()` comparison operation.
- Public `DevelopmentWatchError`, `InvalidWatchRootError`, and `WatchSnapshotError` failure hierarchy.
- Relative subtree ignore support for future output-directory exclusion.

### Watch semantics

- Watcher construction validates the root but performs no recursive scan.
- Snapshots contain regular files and symlinks only; empty directories alone do not produce changes.
- Regular files use SHA-256 content identity rather than timestamp-only detection.
- File bytes are read from a no-follow descriptor when the platform provides `O_NOFOLLOW`.
- File descriptor state and final path state are compared to reject mutation/replacement during snapshotting.
- Symlinks are never traversed; their link target text is fingerprinted and their own inode state is verified.
- Snapshot entries are normalized into deterministic lexical relative-path order.
- Snapshot diffing is pure and classifies `created`, `modified`, and `deleted` paths.
- File↔symlink kind transitions are classified as modifications even when fingerprints happen to match.
- `wait_for_changes()` is explicitly blocking and polling-based; it batches changes until the filesystem settles for the debounce interval.
- No import-time watcher, background global thread, callback executor, build trigger, HTTP-server coupling, or third-party watch dependency is introduced.

### Release

- Advance the development version to `1.1.0b1`.

## [1.1.0a3]

### Added

- Public immutable `BuildManifestDiff` with deterministic `added`, `changed`, `unchanged`, and `removed` classifications.
- Public `diff_build_manifests()` pure comparison operation.
- Public immutable `IncrementalFilesystemWriteResult`.
- Public `FilesystemWriter.write_incremental()` for drift-safe minimal filesystem mutation.
- Public immutable `IncrementalStaticSiteGenerationResult`.
- Public `StaticSiteGenerator.generate_incremental()` orchestration.
- Public `IncrementalOutputDriftError` when tracked output no longer matches the supplied previous manifest.

### Incremental semantics

- Added/changed/unchanged entries preserve the current manifest declaration order.
- Removed entries preserve the previous manifest declaration order.
- A target is unchanged only when both artifact kind and fingerprint are unchanged.
- Every previously tracked output is verified against its prior fingerprint before mutation.
- Missing, manually modified, symlinked, or hard-linked tracked output fails closed before the transaction begins.
- Only added and changed targets are physically written.
- Removed tracked files are transactionally backed up and deleted.
- Unchanged tracked files are not rewritten.
- Unplanned existing files remain untouched.
- Added targets must not overwrite untracked existing files.
- Asset sources may not alias any current or removed output destination.
- Newly written files are fingerprint-verified before transaction commit.
- Failures restore changed and removed files and remove newly added files.
- Empty directories left behind by removed artifacts are intentionally not pruned in this lot.

### Release

- Advance the development version to `1.1.0a3`.

## [1.1.0a2]

### Added

- Public immutable `BuildFingerprint` value object using canonical SHA-256 digests.
- Public immutable `BuildManifestEntry` with explicit `page` / `asset` artifact kinds.
- Public immutable ordered `BuildManifest` with deterministic target lookup.
- Public `build_manifest()` operation for fingerprinting an existing `BuildPlan`.
- Explicit `BuildManifestError`, `InvalidBuildFingerprintError`, `InvalidBuildManifestError`, and `BuildManifestSourceError` exception hierarchy.

### Design

- Page fingerprints hash the exact UTF-8 bytes written by the existing filesystem writer.
- Asset fingerprints stream the exact source bytes instead of using path, timestamp, or file-size identity.
- Asset sources are stat-checked before and after hashing; a source that changes during fingerprinting fails explicitly instead of producing a mixed-content manifest.
- Manifest declaration order remains pages first then assets, matching `BuildPlan`.
- Manifest lookup uses a private immutable sorted index without changing public declaration order.
- Fingerprinting performs no build-output writes, no background work, no watch behavior, and no filesystem cache persistence.
- `API_CONTRACT_1_0.json` remains unchanged; the LOT-38 compatibility gate classifies the new public symbols as compatible additions.

### Release

- Advance the development version to `1.1.0a2`.

## [1.1.0a1]

### Compatibility

- Replace the RC-era exact-runtime equality gate with a post-1.0 compatible-superset comparator.
- Keep `API_CONTRACT_1_0.json` byte-for-byte immutable as the historical compatibility floor.
- Permit compatible minor additions such as new public exports, new members, optional keyword-only parameters, and additive CLI commands/options.
- Reject removal or incompatible mutation of frozen exports, signatures, members, CLI exit semantics, plugin compatibility metadata, and the minimum Python line.
- Convert LOT-37 release checks into historical 1.0 invariants so they remain valid throughout the 1.x line.
- Add adversarial compatibility tests covering both permitted and rejected contract evolution.
- Open the dedicated post-1.0 roadmap in `ROADMAP_1_X.md`.

### Release

- Advance the development version to `1.1.0a1`.
- Generated projects now target the current `1.1.x` compatibility line with an upper bound of `<1.2`.


### Release Engineering

- Add canonical tag-driven publication workflow in `.github/workflows/release.yml`.
- Require stable `vX.Y.Z` tags to match `pypagekit.__version__` exactly before publication.
- Rebuild and smoke-test wheel/sdist from the tagged source before publishing.
- Create/update GitHub Releases from qualified artifacts.
- Publish to PyPI through OIDC Trusted Publishing with the dedicated `pypi` environment.
- Add canonical PyPI project links to package metadata.
- Document the release procedure in `RELEASING.md`.
- Add architecture tests guarding publication workflow invariants.


## [1.0.0]

### Release Qualification

- Advance the package release version from `0.9.0rc1` to `1.0.0` without changing the frozen 1.0 public contract.
- Mark distribution metadata as `Development Status :: 5 - Production/Stable`.
- Add a LOT-37 release gate that verifies the exact LOT-36 `API_CONTRACT_1_0.json` Git blob.
- Keep exact contract regeneration checks across Python 3.11, 3.12, 3.13, and 3.14.
- Qualify wheel metadata, `py.typed`, dependency consistency, and installed CLI entry points.
- Add clean-environment source-distribution installation smoke coverage.
- Add an installed-wheel project scaffold smoke that executes generated `site.py` through `dist/index.html`.
- Generated projects now declare the stable-line requirement `pypagekit>=1.0.0,<1.1`.
- Retain extension compatibility API `0.7`; package and plugin contract versions remain independent.
- Start 1.0.0 with zero active public deprecations.
- Document the final release evidence and post-1.0 boundary in `RELEASE_1_0.md`.

### Compatibility

- No stable Python facade, signature, protocol, exception hierarchy, CLI shell contract, plugin entry-point group, built-in extension ID, typing contract, or minimum Python requirement changes from the LOT-36 baseline.
- The Python/Typer `pypagekit.cli` facade remains explicitly provisional.

## [0.9.0rc1]

### Contract Freeze

- Promote all accepted public Python facades from `stable_candidate` to frozen `stable`.
- Add human-readable 1.0 contract documentation in `API_CONTRACT_1_0.md`.
- Add exact machine-readable 1.0 baseline in `API_CONTRACT_1_0.json`.
- Add deterministic contract snapshot generation through `tools/api_contract_snapshot.py`.
- Add architecture CI requiring exact runtime/baseline equality during the RC-to-1.0 interval.
- Freeze stable facade exports, function/constructor signatures, public class/protocol members, public inheritance relationships, public dataclass semantics, exception hierarchy, enum values, type aliases, and constants.
- Freeze shell CLI commands, root options, entry points, and process exit semantics.
- Freeze plugin entry-point groups, built-in extension IDs, and extension compatibility line `0.7`.
- Freeze PEP 561 typing and minimum supported Python 3.11.
- Keep the Python/Typer `pypagekit.cli` facade explicitly provisional.
- Confirm zero active public deprecations at the 1.0 freeze.
- Normalize standard-library runtime representation differences so one baseline passes identically on Python 3.11, 3.12, 3.13, and 3.14.

### Design

- The frozen contract attaches to canonical public facades, not physical implementation modules.
- Private dataclass fields and internal source-module paths are excluded from the compatibility baseline.
- `pypagekit.__version__` is represented as a version symbol rather than frozen to the RC value, allowing the same contract to qualify `1.0.0`.
- The extension API remains `0.7` because package and plugin compatibility versions are independent.
- Any contract drift between this RC and 1.0 fails CI.
- LOT-37 may finalize release metadata/versioning but must not change the frozen 1.0 contract.

## [0.9.0b1]

### Added

- Canonical compatibility and deprecation policy in `COMPATIBILITY.md`.
- Machine-readable compatibility rules in `COMPATIBILITY.toml`.
- Machine-readable active deprecation registry in `DEPRECATIONS.toml`.
- Canonical migration guide from `0.9.x` to `1.0`.
- Internal deterministic `DeprecationWarning` helper for future compatibility aliases.
- Architecture tests enforcing package-version alignment across public API, compatibility, and deprecation artifacts.
- Architecture tests forbidding silent stable-API removal through the compatibility policy.
- Validation that every future deprecation record has a unique ID and complete migration metadata.
- Explicit compatibility rules for Python facades, CLI contracts, exceptions, typing, and plugin metadata.

### Compatibility

- Adding public surface is compatible when existing semantics remain unchanged.
- Removing or renaming stable facade exports is breaking without a compatibility alias.
- Incompatible signature narrowing is breaking.
- CLI command/option removal or exit-code meaning changes are breaking after freeze.
- Plugin entry-point group and built-in extension ID changes require explicit migration.
- Public type annotations participate in compatibility.
- Security fixes may override normal deprecation timing only when preserving old behavior would keep users exposed.

### Deprecation

- Standard Python `DeprecationWarning` is the canonical warning category.
- Future public deprecations must record ID, kind, public path, since version, replacement, and removal boundary.
- Stable APIs deprecated during `1.x` remain available through the `1.x` major line and become eligible for removal in `2.0.0`.
- PyPageKit `0.9.0b1` has no active public deprecations.

### Design

- LOT-35 defines how the contract evolves; LOT-36 freezes the exact 1.0 contract.
- Deep implementation imports remain outside compatibility guarantees.
- No compatibility aliases are introduced without an actual deprecated public API.
- The extension API remains `0.7`; LOT-35 does not alter plugin qualification compatibility.
- The package advances to `0.9.0b1`.

## [0.9.0a1]

### Added

- Canonical human-readable public API policy in `PUBLIC_API.md`.
- Machine-readable public API inventory in `PUBLIC_API.toml`.
- Explicit stability classifications: `stable_candidate`, `provisional_public`, `operational_contract`, and `internal`.
- Exact inventory of every current public facade `__all__`.
- Explicit operational inventory for CLI commands, process exit semantics, extension entry-point groups, built-in extension IDs, extension API version, PEP 561 typing marker, and minimum Python version.
- Architecture CI that verifies the runtime public exports match the inventory exactly.
- Explicit rule that deep implementation imports are not independent compatibility paths unless promoted by a later compatibility document.

### Design

- Public API stability is attached to documented facade imports rather than physical source-file paths.
- `pypagekit.cli` remains provisional at the Python/Typer adapter level while the shell CLI is tracked as an operational contract.
- The extension facade is a stable candidate, while its compatibility line remains independently versioned as `0.7`.
- LOT-34 freezes the inventory/classification process, not the final 1.0 signatures.
- LOT-35 will define compatibility, deprecation, and migration rules.
- LOT-36 will freeze the accepted 1.0 contract.
- The package advances to `0.9.0a1`.

## [0.8.0b1]

### Performance

- Replace quadratic build-target collision scans with prefix-indexed validation proportional to total path depth.
- Add immutable binary-search indexes for Site route lookup.
- Add immutable binary-search indexes for Assets target lookup.
- Cache ComponentRegistry names and use logarithmic lookup.
- Cache extension registry IDs and component-name projections and use logarithmic lookup.
- Replace assets × destinations inode comparisons with a one-time destination identity index.
- Replace overwrite backup copies with same-directory `os.replace()` snapshots.
- Avoid replacement child-tuple allocation when component runtime traversal makes no changes.
- Replace quadratic duplicate-entry-point counting with one-pass duplicate detection.
- Add deterministic large-collection scalability smoke coverage without wall-clock thresholds.

### Design

- Public declaration ordering and immutable tuple surfaces remain unchanged.
- Private indexes are excluded from public repr/equality semantics.
- Security validation remains in place; performance work does not bypass preflight checks.
- Rollback behavior remains equivalent for Python-observed write failures.
- No parallelism, asynchronous I/O, incremental cache, content hashing, or worker pool is introduced.
- The package advances to `0.8.0b1`.
- Completing LOT-33 closes the `0.8.x — Hardening` implementation line.

## [0.8.0a2]

### Added

- Internal rollback transaction shared by build output and project scaffolding.
- Restoration of overwritten managed files after materialization failure.
- Removal of newly created managed files and directories after materialization failure.
- Explicit `FilesystemRollbackError` when filesystem restoration itself fails.
- Explicit `ProjectScaffoldRollbackError` for failed project restoration.
- `BuildRenderError` with route context for unexpected renderer exceptions.
- Preservation of known PyPageKit renderer exceptions without re-wrapping.
- `InvalidBuildPlanError` when a structural third-party planner violates its return contract.
- `ExtensionFactoryError` for renderer/build-planner factory failures with cause chaining.
- Failure-injection tests for partial writes, overwrites, asset copy interruption, rollback failure, scaffold rollback, renderer failures, invalid planners, and extension factories.

### Design

- Filesystem rollback is scoped to exceptions observed during the active Python operation.
- Unplanned existing files are outside the transaction and remain untouched.
- Overwritten managed files are snapshotted before mutation.
- Newly created managed files and transaction-created directories are removed during rollback.
- Rollback failure is surfaced separately because output consistency can no longer be guaranteed.
- Known framework exceptions preserve their public type.
- Unexpected third-party failures gain framework context while preserving the original exception as the cause.
- No automatic retry policy, crash journal, process supervisor, or background recovery mechanism is introduced.
- The package advances to `0.8.0a2`.

## [0.8.0a1]

### Security

- Reject output-root paths whose existing ancestors are symlinks.
- Reject hard-linked output files before overwrite materialization.
- Detect asset source/output conflicts by filesystem identity, including hard links.
- Reject hard-linked generated project files before `--force` overwrite.
- Reject malformed URL percent escapes and percent-encoded ASCII control characters.
- Detect unsafe schemes after ASCII percent decoding, including encoded-colon obfuscation.
- Reject malformed percent escapes and DEL characters in development-server request paths.
- Add defensive development-server response headers for content sniffing, framing, referrer leakage, caching, and baseline CSP.
- Reject duplicate plugin entry-point identities before loading any provider target.
- Add adversarial coverage for hard links, symlinked output-root ancestors, encoded URL ambiguity, malformed HTTP request paths, response headers, and duplicate entry points.

### Design

- Security hardening strengthens existing boundaries instead of adding privileged bypass APIs.
- Filesystem hardening remains fail-closed before write operations.
- URL validation preserves approved author values rather than normalizing output.
- Development-server headers are local-preview defenses and do not replace deployment security policy.
- Installed plugin Python code is still trusted code once explicit discovery/qualification executes it; LOT-31 reduces avoidable provider execution but does not attempt process sandboxing.
- The package advances to `0.8.0a1`.

## [0.7.0b2]

### Added

- Public extension API compatibility identifier `PYPAGEKIT_EXTENSION_API_VERSION = "0.7"`.
- Optional `ExtensionDescriptor.api_version` compatibility metadata.
- Public `PluginKind`, `PluginState`, `PluginStatus`, and immutable `PluginLifecycle`.
- Explicit lifecycle states: `DISCOVERED`, `QUALIFIED`, `REJECTED`, and `ACTIVE`.
- Explicit qualification through `PluginLifecycle.qualify()`.
- Explicit activation and deactivation through immutable lifecycle transitions.
- Global extension-ID collision detection across renderer, build-planner, and component plugin kinds.
- Compatibility rejection for missing or incompatible extension API declarations.
- Renderer and build-planner factory conformance checks during explicit qualification.
- Structural component-bundle conformance without speculative component instantiation.
- Active-only registry projection through `PluginLifecycle.active_plugins`.
- Qualified registry projection through `PluginLifecycle.qualified_plugins`.
- End-to-end installed-plugin coverage for discovery → qualification → activation → renderer usage.

### Design

- Discovery and qualification remain separate operations.
- A discovered contribution is never automatically active.
- Qualification failures isolate a contribution as `REJECTED` rather than enabling it.
- Lifecycle transitions are immutable and deterministic.
- Plugin activation selects contributions into explicit registries; no third-party lifecycle callback runs.
- Deactivation removes contributions from active registries without unloading Python modules.
- The extension API version is a major.minor contract line, independent from the package release version.
- No process-global mutable registry exists.
- No network lookup, dependency solver, import-time discovery, or hidden activation is introduced.
- Completing LOT-30 closes the `0.7.x — Extensibility` implementation line.

## [0.7.0b1]

### Added

- Explicit installed-plugin discovery through `importlib.metadata.entry_points()`.
- Public `EntryPointDiscovery` service.
- Immutable `PluginDiscoveryResult` containing build-planner, component, and renderer registries.
- Stable entry-point groups:
  - `pypagekit.renderers`;
  - `pypagekit.build_planners`;
  - `pypagekit.components`.
- Zero-argument provider contract for plugin entry points.
- Validation that entry-point names are valid extension IDs.
- Validation that entry-point names exactly match returned extension descriptor IDs.
- Explicit errors for metadata enumeration, target loading, invalid providers, and provider failures.
- Real `*.dist-info/entry_points.txt` integration coverage proving deferred standard-library discovery.

### Design

- Importing PyPageKit performs no plugin discovery.
- Constructing `EntryPointDiscovery` performs no metadata enumeration and loads no plugin module.
- Plugin target imports and provider execution happen only during an explicit `discover()` call.
- Discovery feeds the immutable registries established by LOT-27 and LOT-28 rather than bypassing them.
- Entry-point ordering is normalized deterministically before provider execution.
- Discovery performs no network access.
- No process-global mutable plugin registry is introduced.
- Plugin lifecycle, compatibility negotiation, ordering, activation state, and conformance remain LOT-30.

## [0.7.0a2]

### Added

- Public structural `BuildPlannerProtocol`.
- `StaticSiteGenerator` support for structural planners without mandatory `BuildPlanner` inheritance.
- Immutable `BuildPlannerExtension` and `BuildPlannerRegistry`.
- Immutable `ComponentExtension` and `ComponentExtensionRegistry`.
- Deterministic component contribution aggregation into the existing `ComponentRegistry`.
- Explicit duplicate-component contribution detection across extensions.
- Built-in build-planner registration under `pypagekit.build.planner`.
- Built-in reusable-component bundle under `pypagekit.components.builtin`.
- Integration coverage proving third-party planners and component bundles enter existing runtime paths.

### Design

- LOT-28 extends existing dependency-injection boundaries rather than adding arbitrary build hooks.
- Build planner extensions produce objects satisfying `BuildPlannerProtocol`.
- Component extensions do not bypass `ComponentRegistry` or `ComponentRuntime`.
- Component-name collisions across extension bundles fail explicitly.
- No process-global mutable extension state exists.
- No installed-package scanning or Python entry-point discovery is introduced.
- Plugin discovery remains LOT-29.

## [0.7.0a1]

### Added

- Public `pypagekit.extensions` package.
- Immutable `ExtensionDescriptor` metadata contract.
- Immutable `RendererExtension` contribution model.
- Public immutable `RendererRegistry`.
- Stable namespaced extension IDs using lowercase ASCII dot/hyphen segments.
- Explicit persistent `register()`, lookup, and renderer creation APIs.
- Built-in HTML renderer registration under `pypagekit.renderer.html`.
- Direct integration coverage proving registered renderers flow through `BuildPlanner`.
- Extension-specific validation and registry exceptions.

### Design

- LOT-27 introduces explicit contracts and explicit registration only.
- No process-global mutable extension registry exists.
- No package scanning, import-string loading, or Python entry-point discovery is performed.
- Renderer factories are invoked only when explicitly selected.
- A created renderer must expose a callable `render()` method before entering the build pipeline.
- Existing `BuildPlanner(renderer=...)` dependency injection remains the execution boundary.
- Plugin discovery is deferred to LOT-29 after additional extension points are exercised.

## [0.6.0b2]

### Added

- Public `pypagekit.diagnostics` package.
- Immutable `DiagnosticCheck`, `DiagnosticReport`, `DiagnosticStatus`, and `ProjectInspection` models.
- Read-only `DeveloperDiagnostics` service with deterministic Python, package, project, metadata, and generated-output checks.
- Read-only `ProjectInspector` service that never imports or executes project code.
- `pypagekit doctor [ROOT]` command.
- `pypagekit inspect [ROOT]` command.
- Diagnostic CLI and service coverage plus installed-command smoke checks.
- Generated-project README guidance for diagnostics and inspection.

### Design

- `doctor` classifies checks as PASS, WARNING, or FAIL; warnings do not make a report unhealthy.
- Missing `dist/` output is a warning because generation may not have run yet.
- Missing project definition files and malformed project metadata are failures.
- `inspect` describes filesystem/package facts without loading `site.py`.
- Diagnostics perform no project mutation, subprocess execution, or network access.
- Diagnostics services remain independent from Typer and Rich.

## [0.6.0b1]

### Added

- Public `pypagekit.development` package.
- Immutable `DevelopmentServerConfig` and `DevelopmentServerInfo`.
- Explicit `DevelopmentServer` service and managed `DevelopmentServerSession`.
- Local threaded static HTTP serving using the Python standard library.
- Ephemeral port support in the Python API for deterministic tests and embedding.
- Pretty static URL support through generated directory indexes.
- `Cache-Control: no-store` on development responses.
- Directory listing disabled when no index file exists.
- Request-path confinement to the configured static root.
- Rejection of symlinked static roots, root ancestors, and requested symlink paths.
- Encoded traversal/backslash protections.
- Framework-specific bind/root/host/port errors.
- `pypagekit serve [ROOT]` command with `--host` and `--port`.
- Generated project README guidance for local preview.
- HTTP integration, security, CLI, and installed-command smoke coverage.

### Design

- LOT-25 serves already-generated static output; it does not implicitly build projects.
- The default root is `dist/`, host is `127.0.0.1`, and port is `8000`.
- The development server never changes the process current working directory.
- Typer remains an adapter over the development service.
- The server is intentionally local/static: no watch mode, hot reload, project loading, browser auto-open, TLS, or production-server claims are introduced.
- Development services remain independent from Typer and Rich.


## [0.6.0a2]

### Added

- Public `pypagekit.project` application-service package.
- Immutable `ProjectFile`, `ProjectPlan`, and `ProjectScaffoldResult` models.
- Public `ProjectScaffolder` with explicit plan-then-write workflow.
- Deterministic minimal scaffold containing `.gitignore`, `README.md`, `pyproject.toml`, and executable `site.py`.
- Project-name normalization derived from the target directory or an explicit project name.
- Generated project dependency constrained to the current PyPageKit `0.6.x` release line.
- Safe-by-default protection for existing scaffold-managed files.
- Explicit `force=True` / CLI `--force` replacement policy for regular managed files.
- Symlink protections for target roots, target-root ancestors, and managed target files.
- `pypagekit new TARGET` command.
- CLI translation of scaffolding failures to stderr with execution exit code `1`.
- Unit, integration, security, and installed-command help coverage.

### Design

- The Typer command is a thin adapter over `ProjectScaffolder`.
- Project planning is independent from Typer and Rich.
- Existing unplanned files inside a target directory are preserved.
- Scaffold preflight completes before predictable writes begin.
- The generated `site.py` uses the existing Python API and `StaticSiteGenerator` directly.
- LOT-24 does not introduce a project loader, CLI build command, development server, or diagnostics subsystem.


## [0.6.0a1]

### Added

- Typer 0.27.x as the canonical CLI framework.
- Rich 15.x as the canonical human-facing terminal presentation layer.
- Installed `pypagekit` console entry point.
- `python -m pypagekit` module entry point.
- Root `--help` / `-h` support.
- Eager root `--version` support.
- Centralized Rich stdout/stderr consoles with markup and automatic highlighting disabled.
- Stable CLI exit-code constants: success `0`, execution error `1`, usage error `2`.
- Explicit command-registration boundary for subsequent CLI LOTs.
- CLI integration tests using Typer's `CliRunner`.
- Architecture tests preventing Typer/Rich dependencies from leaking into core packages.
- Installed-wheel CLI smoke coverage.

### Design

- Typer parses CLI intent; Rich presents human-readable output; PyPageKit core remains authoritative for behavior.
- `import pypagekit` does not import Typer or Rich.
- No workflow command is advertised before its dedicated LOT implements it.
- CLI usage failures retain Typer/Click's exit-code `2` semantics.
- The root package remains usable independently from the CLI.
- LOT-23 establishes CLI infrastructure only; project scaffolding, serving, and diagnostics remain LOT-24 through LOT-26.


## [0.5.0b2]

### Added

- Public `StaticSiteGenerator` end-to-end static-site generation facade.
- Immutable `StaticSiteGenerationResult` retaining both `BuildPlan` and `FilesystemWriteResult`.
- Explicit orchestration of `Site + Assets → BuildPlanner → BuildPlan → FilesystemWriter`.
- Optional dependency injection for planner and writer.
- Result projections for output root, page files, asset files, and all generated files.
- LOT-22 unit, integration, and security coverage.

### Design

- `StaticSiteGenerator` is an orchestration layer only.
- It delegates all route mapping and rendering to `BuildPlanner`.
- It delegates all filesystem materialization and safety policy to `FilesystemWriter`.
- Existing build and filesystem exceptions propagate unchanged instead of being hidden behind a generic generation error.
- Planning always completes before filesystem writing begins.
- The generated result preserves both planning evidence and write evidence.
- Completing LOT-22 closes the `0.5.x — Static Build` implementation line.


## [0.5.0b1]

### Added

- Public `FilesystemWriter` for materializing a qualified `BuildPlan`.
- Immutable `FilesystemWriteResult` reporting page and asset files written.
- Explicit `output_root` boundary supplied at write time.
- Recursive output-directory creation.
- UTF-8 page output.
- Binary asset copying from declared `Asset.source`.
- Safe-by-default no-overwrite behavior with explicit `overwrite=True`.
- Full preflight for output-root type, existing targets, target ancestors, asset sources, and source/output overlap.
- Symlink rejection for output root, target ancestors, and target files.
- Filesystem-specific output errors.
- LOT-21 unit, integration, and security coverage.

### Security

- Existing targets are never overwritten unless explicitly requested.
- Default writes use exclusive creation modes to protect against post-preflight target creation.
- Symlinked output roots and target paths are rejected even when overwrite is enabled.
- Asset sources may not coincide with any planned output destination.
- Missing, broken, or non-file asset sources fail before output directories are created.
- Predictable filesystem conflicts are detected before any materialization starts.

### Design

- LOT-21 executes a precomputed `BuildPlan`; it does not decide routes, render pages, or recalculate targets.
- Unplanned existing files under the output root are preserved.
- No global clean/delete operation is introduced.
- Asset bytes are copied as-is; bundling, hashing, fingerprinting, and transformations remain outside this LOT.
- End-to-end `Site + Assets → output tree` orchestration remains LOT-22.


## [0.5.0a2]

### Added

- Public `pypagekit.build` planning API.
- Immutable `PageBuildEntry`, `AssetBuildEntry`, and `BuildPlan`.
- Public `BuildPlanner` consuming `Site` and optional `Assets`.
- Pretty static route mapping: `/ -> index.html`, `/about -> about/index.html`.
- Page rendering into in-memory build entries through an injected `Renderer`.
- Deterministic page-first / asset-second target ordering.
- Structural target-collision detection for exact duplicates and file/directory conflicts.
- Build-specific validation and collision errors.
- LOT-20 unit, integration, and security coverage.

### Design

- LOT-20 implements plan-first, write-second.
- Page HTML is rendered into memory during planning, but no output file is created.
- Asset build entries carry declarative source/target information without reading source bytes.
- Target collisions are detected before page rendering starts.
- Route-to-output mapping remains separate from logical `Route.path`.
- `BuildPlan` contains no output root and exposes no write/execute operation.
- Filesystem materialization remains LOT-21.


## [0.5.0a1]

### Added

- Public immutable `Asset(source, target)` declaration.
- Public immutable `Assets` collection with deterministic ordering and target lookup.
- Root-relative `Asset.public_path` derived from a validated POSIX publish target.
- Duplicate publish-target detection.
- Strict portable asset-target validation for traversal, separators, controls, query/fragment markers, colon characters, and percent-encoded ambiguity.
- Asset-specific validation and lookup errors.
- LOT-19 unit and security coverage.

### Design

- Asset sources are `pathlib.Path` values but are never opened, stat'ed, copied, or validated for existence in LOT-19.
- Asset targets are `PurePosixPath` values relative to the future output root.
- Multiple asset declarations may reuse one source when their targets differ.
- `Assets` remains independent from `Site`; LOT-20 will combine logical site and asset declarations into build planning.
- Public asset references are logical root-relative paths, not filesystem output operations.
- No directory creation, copying, hashing, fingerprinting, bundling, or file writing is introduced.


## [0.4.0b1]

### Added

- Public immutable `Site` aggregate owning canonical `Route` objects.
- Public immutable `Sitemap` and `SitemapEntry` domain projections.
- Deterministic site path/page projections and logical-route lookup.
- Duplicate canonical route-path detection across a site or standalone sitemap.
- Optional site-level `Navigation` association.
- Validation that navigation routes belong to the site and reference the site's canonical route objects.
- Sitemap derivation from every site route, including routes absent from navigation.
- Site-specific validation errors.
- LOT-18 unit and security coverage.

### Design

- `Site` is the canonical owner of route objects for a site definition.
- Navigation may expose a subset of site routes but may not introduce external routes.
- Navigation must reference the exact immutable `Route` objects owned by the site.
- Sitemap is a domain projection, not XML serialization.
- Site lookup canonicalizes logical route input through the existing route validator.
- No filesystem path, build plan, file writing, or sitemap XML output is introduced.
- Completing LOT-18 closes the `0.4.x — Routing & Site` implementation line.


## [0.4.0a2]

### Added

- Public immutable `NavigationItem` referencing a `Route` with ordered child items.
- Public immutable `Navigation` aggregate for validated hierarchical navigation trees.
- Depth-first navigation traversal helpers.
- Deterministic route and route-path projection from navigation trees.
- Duplicate-route detection across an entire navigation tree.
- Identity-based navigation-cycle detection.
- Navigation-specific validation errors.
- LOT-17 unit and security coverage.

### Design

- Navigation references `Route` objects directly and never duplicates raw URL strings.
- Labels remain raw semantic strings; HTML escaping is a future rendering concern.
- Duplicate labels are valid when they reference distinct routes.
- A canonical route path may appear only once within a single navigation tree.
- Navigation performs no rendering, filesystem work, sitemap generation, or active-route selection.
- Site-wide route existence and sitemap consistency remain LOT-18 concerns.


## [0.4.0a1]

### Added

- Public immutable `Route` associating a canonical logical URL path with a `Page`.
- Public `normalize_route_path()` helper in `pypagekit.domain`.
- Root-route and ordered path-segment inspection.
- Canonical removal of a non-root trailing slash.
- Route validation for absolute internal paths.
- Explicit route errors for invalid paths and non-`Page` targets.
- LOT-16 unit and security coverage.

### Security

- External and protocol-relative URLs are rejected.
- Query strings and fragments are rejected, including empty markers.
- Empty path segments and backslash separators are rejected.
- Literal and percent-encoded `.` / `..` traversal segments are rejected.
- Percent-encoded slash, backslash, and control-character ambiguity is rejected.
- Invalid percent escapes are rejected.

### Design

- `Page != Route != filesystem output path`.
- A route describes logical site location only.
- Route construction performs no rendering, filesystem I/O, redirect handling, navigation generation, or output-path planning.
- Duplicate route detection remains a `Site` concern for LOT-18.


## [0.3.0b3]

### Added

- Public immutable `ComponentRef(Content)` symbolic component reference.
- Public immutable `ComponentRegistry` under `pypagekit.components`.
- Stable lowercase kebab-case registry names.
- Deterministic normalized keyword properties for component references.
- Persistent `register()` API that returns a new registry instead of mutating the existing instance.
- Explicit factory lookup and component instantiation.
- `ComponentRuntime(registry=...)` support for resolving `ComponentRef`.
- Registry-specific errors for duplicates, unknown names, missing registries, invalid names/properties, and invalid factory results.
- LOT-15 unit, integration, and security coverage.

### Design

- There is no process-global or module-global mutable component registry.
- Symbolic references resolve only through a registry explicitly supplied to `ComponentRuntime`.
- The registry stores callables but does not perform dynamic imports or module discovery.
- Registered components enter the existing `Component → Content → HtmlRenderer` pipeline after instantiation.
- Factory argument errors remain visible instead of being silently coerced or swallowed.
- Completing LOT-15 closes the `0.3.x — Components` implementation line.


## [0.3.0b2]

### Added

- Public wrapperless `Fragment(Content)` composition primitive.
- Public named `Slot(Content)` placeholders with optional fallback content and required-slot semantics.
- Immutable deterministic `SlotBindings` for explicit named injections.
- Public abstract `SlottedComponent` with final slot-aware composition.
- Public `bind_slots()` helper for explicit template composition.
- Slot support inside `LayoutRegion` through `Layout.slot_bindings()`.
- Runtime traversal of fragments and explicit rejection of unresolved slots.
- Wrapperless fragment rendering in `HtmlRenderer`.
- LOT-14 domain, runtime, layout, rendering, and security coverage.

### Design

- Slots are lexical to the template that declares them; bindings do not implicitly cross component boundaries.
- Slot names use validated lowercase kebab-case and must be unique within one template.
- Unknown bindings fail explicitly instead of being silently ignored.
- Required slots require an explicit binding and cannot define fallback content.
- Explicit empty bindings are distinct from missing bindings and intentionally render nothing.
- A slot may inject zero, one, or many content nodes without introducing a wrapper element.
- Slots remain composition concerns; no HTML representation exists for an unresolved slot.
- Global component lookup and registration remain deferred to LOT-15.


## [0.3.0b1]

### Added

- Public built-in reusable components: `Section`, `Card`, and `Hero`.
- Immutable normalization of reusable-component child content.
- Configurable semantic heading levels for built-in titled components.
- Independent outer-container and heading `Attributes` hooks.
- Support for nested custom components inside reusable components.
- LOT-13 unit, integration, and security coverage.

### Design

- Built-in components are exported from `pypagekit.components`, not from the package root.
- Reusable components compose only existing core primitives; they introduce no new rendering path.
- `Section` composes a required heading followed by ordered child content.
- `Card` composes an optional heading followed by ordered child content.
- `Hero` composes a heading, optional paragraph body, and optional `Link` action.
- No implicit CSS class, data marker, style, or JavaScript behavior is attached to built-in components.
- Dynamic slots remain deferred to LOT-14.


## [0.3.0a2]

### Added

- Public abstract `Layout(Component)` model.
- Public immutable `LayoutRegion(Content)` for ordered named structural regions.
- Lowercase kebab-case validation for region names.
- Duplicate-region detection within a layout.
- Recursive component resolution inside layout regions.
- Neutral HTML representation using `data-layout-region`.
- LOT-12 domain, runtime, rendering, and security coverage.

### Design

- Layouts organize structure; they do not define CSS, grids, breakpoints, or visual styling.
- `Layout.regions()` declares ordered structural regions and `Layout.compose()` turns them into ordinary content.
- Region names are unique within one layout.
- Region attributes remain controlled through the existing `Attributes` model.
- The renderer chooses a neutral `div[data-layout-region]` representation.
- Slots remain deferred to LOT-14; LOT-12 regions are statically declared by the layout implementation.


## [0.3.0a1]

### Added

- Public abstract `Component(Content)` model with `compose() -> Content`.
- Public `ComponentRuntime` for explicit component resolution.
- Recursive resolution of components returned directly or nested inside containers.
- Runtime validation that `compose()` returns `Content`.
- Identity-based component cycle detection.
- Configurable component-resolution depth guard for recursively generated components.
- Transparent `HtmlRenderer` integration through the component runtime.
- LOT-11 tests for composition, nesting, immutability boundaries, cycles, depth protection, escaping, and URL security.

### Design

- Components compose domain structure; they do not render HTML.
- The renderer resolves a component to ordinary content before applying the existing rendering pipeline.
- `Component` remains a `Content`, so it can already appear anywhere `Page` or `Container` accepts content.
- The runtime recreates a container only when one of its descendants actually resolves to different content.
- Layouts, reusable component catalogues, slots, and registries remain outside LOT-11.


## [0.2.0b3]

### Added

- Public immutable `Attributes` model for controlled author-facing HTML hooks.
- Support for `id`, ordered CSS class tokens, `title`, `data-*`, and `aria-*`.
- Attribute support on `Heading`, `Paragraph`, `Container`, `Link`, and `Image`.
- Internal domain-to-HTML attribute mapping that preserves intrinsic attributes such as `href`, `src`, and `alt`.
- Validation for class tokens and data/ARIA attribute suffixes.
- Integration and security coverage for deterministic rendering and attribute injection resistance.

### Security

- No arbitrary attribute dictionary is exposed by the domain model.
- Event-handler attributes and inline `style` are not part of the LOT-10 API.
- Author values remain semantic strings and are escaped at the HTML serialization boundary.
- `data-*` and `aria-*` names are namespaced from validated lowercase suffixes.

### Design

- `Text` remains a text fragment and therefore has no attribute surface.
- Intrinsic link/image attributes remain owned by `Link` and `Image`, not by `Attributes`.
- Class token order is preserved; data/ARIA mappings are normalized deterministically.
- The generic attribute surface remains intentionally narrow until real component use cases justify expansion.


## [0.2.0b2]

### Added

- Rendering of `Page.description` as a deterministic HTML meta description.
- Dedicated head-content assembly preserving the order `charset → title → description`.
- Integration tests for optional, empty, escaped, and deterministic description metadata.
- Security coverage proving description metadata cannot break out of its attribute context.

### Design

- The existing `Page` metadata model remains intentionally small: `title`, `lang`, and optional `description`.
- `description=None` emits no meta description.
- `description=""` remains explicitly representable.
- Metadata values remain semantic domain strings and are escaped only at the HTML serialization boundary.
- Canonical URLs, stylesheets, additional head entries, and richer metadata remain outside LOT-09.


## [0.2.0b1]

### Added

- Render-time URL safety validation for links and images.
- Explicit allowlists for link schemes (`http`, `https`, `mailto`) and image schemes (`http`, `https`).
- `SecurityError` and `UnsafeUrlError` rendering exceptions.
- Adversarial XSS tests covering active markup, attribute breakout attempts, nested composition, unsafe URL schemes, control characters, and pre-escaped input.

### Security

- Relative references, anchors, query references, and protocol-relative references remain supported.
- Active or local-resource schemes such as `javascript:`, `data:`, `vbscript:`, `file:`, and unsupported schemes are rejected at render time.
- URL values remain semantic domain strings and are validated before attribute-context escaping.
- ASCII control characters are rejected in URL references.
- Text and attribute escaping continue to happen exactly at the HTML boundary.
- No `RawHtml`, `SafeHtml`, `escape=False`, or equivalent bypass is introduced.

### Design

- URL safety belongs to the rendering/security boundary rather than mutating the domain model.
- Validation returns the original URL value after approval; output normalization is not performed.
- The serializer remains syntax-focused and does not own URL policy.


## [0.2.0a2]

### Added

- Public `Renderer` protocol.
- Public `HtmlRenderer` implementation.
- Explicit domain-to-HTML dispatch for `Text`, `Heading`, `Paragraph`, `Container`, `Link`, `Image`, and `Page`.
- Recursive ordered rendering for composition trees.
- Complete compact HTML5 document rendering for `Page`.
- `UnsupportedNodeError` for domain nodes not supported by the renderer.
- LOT-07 unit and integration coverage for fragments, nested trees, complete documents, determinism, escaping, and unsupported nodes.

### Design

- `HtmlRenderer.render(node) -> str` is the first public representation contract.
- Domain objects remain renderer-agnostic and never render themselves.
- `Container` maps to `div` in the initial HTML renderer.
- `Page` emits doctype, `html lang`, UTF-8 charset, `title`, and `body`.
- Richer page metadata such as `description` remains deferred to LOT-09.
- URL scheme safety remains deferred to LOT-08; LOT-07 still benefits from attribute-context escaping supplied by LOT-06.
- Rendering performs no filesystem or network I/O.

## [0.2.0a1]

### Added

- Pure HTML5 text and attribute escaping primitives.
- Deterministic serialization for ordinary HTML elements.
- Canonical serialization for HTML5 void elements.
- HTML5 doctype serialization.
- Structural validation for tag and attribute names.
- Scalar and boolean HTML attribute serialization.
- Rendering/serialization exception hierarchy.
- LOT-06 tests for escaping, determinism, Unicode, void elements, boolean attributes, and invalid structural names.

### Design

- Serialization is domain-agnostic and performs no filesystem or network I/O.
- Element content is treated as a trusted serialized fragment; semantic user text must cross the explicit text-escaping boundary first.
- Attribute order is canonicalized lexicographically for deterministic output.
- `None` and `False` omit attributes, `True` emits a name-only boolean attribute, and empty strings are preserved.
- `script` and `style` are rejected by the generic element serializer because they require dedicated raw-text contexts.
- The serializer is implementation infrastructure and is not exported from the package root.
- Domain-to-HTML mapping remains deferred to LOT-07.

## [0.1.0b1]

### Added

- `Action` and `Media` semantic base types in the domain namespace.
- Immutable `Link` action content primitive.
- Immutable `Image` media content primitive.
- Structural validation for empty link destinations and image sources.
- `InvalidLinkHrefError` and `InvalidImageSourceError`.
- LOT-05 tests covering composition, immutability, Unicode, destination/source forms, and decorative images.

### Design

- `Link.label`, `Link.href`, `Image.src`, and `Image.alt` preserve authored strings exactly.
- Empty link labels remain representable.
- Empty image `alt` values are explicitly valid for decorative images.
- URL scheme safety is intentionally deferred to the rendering/security boundary in LOT-08 rather than embedded in the domain model.

## [0.1.0a4]

### Added

- Immutable `Container` content primitive for ordered composition trees.
- Iterable-to-tuple normalization for container children.
- Recursive composition through nested `Container` instances.
- `InvalidContainerChildError` for non-`Content` children.
- LOT-04 tests covering order, generators, nesting, immutability, validation, and input isolation.

### Design

- Empty containers are valid.
- `Container` models composition only; it introduces no rendering, layout, HTML, filesystem, or component-runtime behavior.
- Child order is author-defined and preserved exactly.

## [0.1.0a3]

### Added

- Immutable `Text`, `Heading`, and `Paragraph` content primitives.
- Heading level validation restricted to semantic levels `1..6`.
- `InvalidHeadingLevelError` in the domain validation hierarchy.
- Public package exports for text content primitives.
- LOT-03 unit test coverage for raw text preservation, Unicode, immutability, type validation, and heading levels.

### Design

- Text values remain raw domain values and are not HTML-escaped at construction time.
- Empty text values remain representable; rendering and higher-level conformance rules may decide how they are used.

## [0.1.0a2]

### Added

- `Node` and `Content` core domain abstractions.
- Immutable `Page` root document object with ordered content.
- Domain exception hierarchy with page-specific validation errors.
- Validation for page title, language, description type, and content membership.
- LOT-02 unit test suite.

## [0.1.0a1]

### Added

- Repository bootstrap for LOT-01.
- `src/` package layout.
- PEP 561 `py.typed` marker.
- Initial package metadata.
- Pytest, Ruff, and mypy configuration.
- GitHub Actions quality and packaging workflow.
