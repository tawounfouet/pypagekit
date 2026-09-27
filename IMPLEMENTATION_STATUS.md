# PyPageKit Implementation Status

| LOT | Scope | Status | Target |
|---|---|---|---|
| LOT-01 | Project Foundations | QUALIFIED | `0.1.0a1` |
| LOT-02 | Core Domain Foundations | QUALIFIED | `0.1.0a2` |
| LOT-03 | Text Content | QUALIFIED | `0.1.0a3` |
| LOT-04 | Composition Tree | QUALIFIED | `0.1.0a4` |
| LOT-05 | Actions & Media | QUALIFIED | `0.1.0b1` |
| LOT-06 | HTML Serialization | QUALIFIED | `0.2.0a1` |
| LOT-07 | HTML Renderer | QUALIFIED | `0.2.0a2` |
| LOT-08 | Security & Escaping | QUALIFIED | `0.2.0b1` |
| LOT-09 | Page Metadata | QUALIFIED | `0.2.0b2` |
| LOT-10 | Attributes & Styling Hooks | QUALIFIED | `0.2.0b3` |
| LOT-11 | Component Model | QUALIFIED | `0.3.0a1` |
| LOT-12 | Layout Model | QUALIFIED | `0.3.0a2` |
| LOT-13 | Reusable Components | QUALIFIED | `0.3.0b1` |
| LOT-14 | Slots & Composition | QUALIFIED | `0.3.0b2` |
| LOT-15 | Component Registry | QUALIFIED | `0.3.0b3` |
| LOT-16 | Route Model | QUALIFIED | `0.4.0a1` |
| LOT-17 | Navigation Model | QUALIFIED | `0.4.0a2` |
| LOT-18 | Sitemap & Site Model | QUALIFIED | `0.4.0b1` |
| LOT-19 | Assets | QUALIFIED | `0.5.0a1` |
| LOT-20 | Build Pipeline | QUALIFIED | `0.5.0a2` |
| LOT-21 | Filesystem Output | QUALIFIED | `0.5.0b1` |
| LOT-22 | Static Site Generation | QUALIFIED | `0.5.0b2` |
| LOT-23 | CLI Foundations | QUALIFIED | `0.6.0a1` |
| LOT-24 | Project Scaffolding | QUALIFIED | `0.6.0a2` |
| LOT-25 | Development Server | QUALIFIED | `0.6.0b1` |
| LOT-26 | Developer Diagnostics | QUALIFIED | `0.6.0b2` |
| LOT-27 | Extension Contracts & Renderer Registry | QUALIFIED | `0.7.0a1` |
| LOT-28 | Build & Component Extension Points | QUALIFIED | `0.7.0a2` |
| LOT-29 | Plugin Discovery & Entry Points | QUALIFIED | `0.7.0b1` |
| LOT-30 | Plugin Lifecycle & Conformance | QUALIFIED | `0.7.0b2` |
| LOT-31 | Security Hardening | QUALIFIED | `0.8.0a1` |
| LOT-32 | Reliability & Failure Hardening | QUALIFIED | `0.8.0a2` |
| LOT-33 | Performance & Scalability Hardening | QUALIFIED | `0.8.0b1` |
| LOT-34 | Public API Inventory & Stability Classification | QUALIFIED | `0.9.0a1` |
| LOT-35 | Compatibility, Deprecation & Migration | QUALIFIED | `0.9.0b1` |
| LOT-36 | 1.0 Contract Freeze | QUALIFIED | `0.9.0rc1` |
| LOT-37 | 1.0 Release Qualification | IN QUALIFICATION | `1.0.0` |

## LOT-07 exit criteria

- [x] public `Renderer` protocol exists
- [x] public `HtmlRenderer` implementation exists
- [x] `Text` renders as escaped text
- [x] `Heading` maps levels 1 through 6 to `h1` through `h6`
- [x] `Paragraph` maps to `p`
- [x] `Container` maps to `div` and renders children recursively
- [x] `Link` maps to `a`
- [x] `Image` maps to HTML5 `img`
- [x] `Page` renders a complete compact HTML5 document
- [x] page language and title are serialized safely
- [x] UTF-8 charset is present
- [x] unsupported nodes fail explicitly
- [x] rendering is deterministic
- [x] rendering does not mutate domain objects
- [x] renderer performs no filesystem or network I/O
- [x] `Page.description` remains deferred to LOT-09
- [x] URL scheme policy remains deferred to LOT-08
- [x] integration tests prove `Page → HTML`

Next: **LOT-09 — Page Metadata**.

## LOT-07 qualification evidence

- branch implementation prepared for CI qualification
- first end-to-end in-memory `Page → HTML` flow now exists
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-08 exit criteria

- [x] text content remains escaped by default
- [x] attribute values remain escaped in attribute context
- [x] link destinations use an explicit scheme allowlist
- [x] image sources use an explicit scheme allowlist
- [x] relative, anchor, query, and protocol-relative references remain supported
- [x] active/local-resource URL schemes are rejected
- [x] ASCII control characters in URL references are rejected
- [x] mixed-case unsafe schemes are rejected
- [x] whitespace-obfuscated unsafe schemes are rejected
- [x] nested composition does not bypass escaping
- [x] page title cannot break out into markup
- [x] attribute breakout payloads remain inert
- [x] no raw-HTML or escape-disable bypass exists
- [x] pre-escaped strings are not treated as trusted HTML
- [x] security policy does not mutate domain values
- [x] adversarial security tests cover the complete current rendering pipeline

Next: **LOT-09 — Page Metadata**.

## LOT-08 qualification evidence

- dedicated `tests/security/` corpus added
- URL validation occurs before HTML attribute serialization
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-09 exit criteria

- [x] page title remains rendered in `<title>`
- [x] page language remains rendered on the root `html` element
- [x] UTF-8 charset remains first in the head
- [x] optional page description renders as `<meta name="description">`
- [x] absent description emits no metadata element
- [x] empty description remains explicitly representable
- [x] description values are attribute-escaped safely
- [x] description metadata cannot inject active markup or attributes
- [x] head metadata ordering is deterministic
- [x] rendering does not mutate page metadata
- [x] no new metadata abstraction is introduced prematurely

Next: **LOT-10 — Attributes & Styling Hooks**.

## LOT-09 qualification evidence

- existing `Page` metadata fields are now fully represented in HTML
- deterministic head assembly is covered by integration tests
- security corpus covers description attribute breakout attempts
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-10 exit criteria

- [x] public immutable `Attributes` value object exists
- [x] `id`, class tokens, and `title` are supported
- [x] `data-*` hooks are generated from validated suffixes
- [x] `aria-*` hooks are generated from validated suffixes
- [x] classes preserve declaration order
- [x] data/ARIA mappings normalize deterministically
- [x] `Heading`, `Paragraph`, `Container`, `Link`, and `Image` accept attributes
- [x] `Text` remains attribute-free
- [x] intrinsic `href`, `src`, and `alt` remain controlled by their domain objects
- [x] arbitrary event-handler and style keywords are not supported
- [x] author values are escaped at serialization time
- [x] existing output is unchanged when attributes are omitted
- [x] rendering remains deterministic
- [x] adversarial tests cover attribute breakout attempts

Next: **LOT-11 — Component Model**.

## LOT-10 qualification evidence

- controlled domain attribute surface added without `dict[str, Any]`
- renderer maps domain hooks to serializer attributes through an internal adapter
- security corpus covers id/class/title/data/aria injection attempts
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-11 exit criteria

- [x] public abstract `Component` derives from `Content`
- [x] `Component.compose() -> Content` is the composition contract
- [x] components have no rendering method
- [x] public `ComponentRuntime` resolves components explicitly
- [x] components may return ordinary content
- [x] components may return other components
- [x] components nested inside containers resolve recursively
- [x] invalid compose results fail explicitly
- [x] direct component cycles are detected
- [x] indirect component cycles are detected
- [x] fresh recursive component generation is bounded by max depth
- [x] unchanged ordinary content preserves identity
- [x] source containers are not mutated during resolution
- [x] `HtmlRenderer` resolves components before HTML mapping
- [x] existing escaping and URL security still apply to component output
- [x] layouts, slots, registry, and reusable component catalogues remain deferred

Next: **LOT-12 — Layout Model**.

## LOT-11 qualification evidence

- component composition remains domain-first and renderer-independent
- explicit runtime isolates composition resolution from HTML serialization
- integration tests cover `Component → Content → HtmlRenderer`
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-12 exit criteria

- [x] public abstract `Layout` derives from `Component`
- [x] public immutable `LayoutRegion` derives from `Content`
- [x] regions preserve declaration order
- [x] region names use validated lowercase kebab-case
- [x] region names are unique within a layout
- [x] region children normalize to immutable tuples
- [x] regions accept controlled `Attributes`
- [x] components nested inside regions resolve recursively
- [x] runtime preserves unchanged region identity
- [x] runtime recreates regions only when descendant resolution changes
- [x] renderer chooses a neutral representation with `data-layout-region`
- [x] intrinsic region marker cannot be spoofed through generic data hooks
- [x] no CSS/grid/breakpoint semantics are introduced
- [x] no dynamic slot API is introduced prematurely
- [x] security tests cover region names and attribute values

Next: **LOT-13 — Reusable Components**.

## LOT-12 qualification evidence

- layout semantics remain domain-first and renderer-independent
- regions compose through the existing component runtime
- rendering stays neutral and deterministic
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-13 exit criteria

- [x] public built-in reusable component catalogue exists
- [x] `Section`, `Card`, and `Hero` derive from `Component`
- [x] built-ins compose only existing core content primitives
- [x] reusable child collections normalize to immutable tuples
- [x] title/body/action inputs have explicit type validation
- [x] semantic heading levels remain configurable and validated
- [x] outer and heading attributes use the existing controlled `Attributes` model
- [x] no implicit CSS classes or component markers are emitted
- [x] reusable components may contain custom components
- [x] reusable components may be nested
- [x] reusable components work inside layouts and pages
- [x] rendering continues through `ComponentRuntime → HtmlRenderer`
- [x] text/attribute escaping still applies
- [x] URL security still applies to reusable component actions
- [x] no raw-HTML escape hatch is introduced
- [x] dynamic slots remain deferred to LOT-14

Next: **LOT-14 — Slots & Composition**.

## LOT-13 qualification evidence

- built-in catalogue is composition-only and renderer-independent
- integration tests prove reuse inside pages, layouts, and custom component trees
- security tests prove built-ins inherit the existing rendering safety boundary
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-14 exit criteria

- [x] public wrapperless `Fragment` content primitive exists
- [x] public named `Slot` placeholder exists
- [x] slot names use validated lowercase kebab-case
- [x] slot fallback content normalizes to immutable tuples
- [x] required slots require explicit bindings
- [x] required slots cannot define fallback content
- [x] immutable deterministic `SlotBindings` exists
- [x] explicit empty binding is distinct from missing binding
- [x] unknown bindings fail explicitly
- [x] duplicate slot names fail explicitly
- [x] public `SlottedComponent` composes templates through slot bindings
- [x] layouts can bind slots declared inside regions
- [x] slot replacement preserves source-tree immutability
- [x] bound content may contain components resolved by `ComponentRuntime`
- [x] fragments render without wrapper elements
- [x] unresolved slots fail explicitly in runtime and renderer
- [x] text/attribute escaping still applies to injected content
- [x] URL security still applies to injected actions
- [x] no raw-HTML bypass is introduced
- [x] slots remain lexical and no global registry is introduced

Next: **LOT-15 — Component Registry**.

## LOT-14 qualification evidence

- named injection is explicit and deterministic
- multi-node slot content renders wrapperlessly through `Fragment`
- runtime/security tests cover resolved and unresolved slot paths
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-15 exit criteria

- [x] public immutable `ComponentRef` exists
- [x] component names use validated lowercase kebab-case
- [x] component reference properties normalize deterministically
- [x] invalid keyword property names fail explicitly
- [x] public immutable `ComponentRegistry` exists
- [x] registry names are deterministic
- [x] registration returns a new registry instead of mutating the source
- [x] duplicate registrations fail explicitly
- [x] unknown components fail explicitly
- [x] registered factories must return `Component`
- [x] runtime requires an explicit registry for symbolic references
- [x] symbolic references resolve inside nested content trees
- [x] renderer works through an injected registry-aware runtime
- [x] text escaping and URL security still apply after registry resolution
- [x] no global mutable registry exists
- [x] no dynamic import or implicit module discovery exists

Next: **LOT-16 — Route Model**.

## LOT-15 qualification evidence

- registry resolution is explicit, local, and deterministic
- symbolic references enter the existing component/runtime/rendering pipeline
- security tests cover malicious text, URLs, and registry names
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-16 exit criteria

- [x] public immutable `Route` exists
- [x] route associates a canonical logical path with exactly one `Page`
- [x] root route `/` is explicitly representable
- [x] non-root trailing slash canonicalizes deterministically
- [x] route segments are available without filesystem interpretation
- [x] route paths must be absolute internal URL paths
- [x] external and protocol-relative URLs fail explicitly
- [x] queries and fragments fail explicitly
- [x] duplicate slash segments fail explicitly
- [x] literal and encoded traversal segments fail explicitly
- [x] encoded slash/backslash/control ambiguity fails explicitly
- [x] malformed percent escapes fail explicitly
- [x] route target must be a `Page`
- [x] route validation performs no filesystem or rendering work
- [x] duplicate-route detection remains deferred to the future `Site` aggregate

Next: **LOT-17 — Navigation Model**.

## LOT-16 qualification evidence

- route identity is independent from page rendering and future build output
- validation covers canonicalization plus URL/path-confusion cases
- security corpus covers externalization, traversal, encoded separators, and fragment/query confusion
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-17 exit criteria

- [x] public immutable `NavigationItem` exists
- [x] each navigation item references a `Route` object
- [x] labels are required semantic strings and preserve authored values
- [x] child navigation items preserve declaration order
- [x] child iterables normalize to immutable tuples
- [x] public immutable `Navigation` exists
- [x] empty navigation is valid
- [x] navigation traversal is deterministic and depth-first
- [x] route projection preserves navigation tree order
- [x] duplicate route paths fail explicitly across the whole tree
- [x] duplicate labels remain valid for distinct routes
- [x] object cycles fail explicitly
- [x] route validation/security cannot be bypassed through navigation
- [x] navigation performs no HTML rendering or filesystem work
- [x] site membership and sitemap consistency remain deferred to LOT-18

Next: **LOT-18 — Sitemap & Site Model**.

## LOT-17 qualification evidence

- navigation owns hierarchy and labels while routes remain the single source of logical URL identity
- tree validation covers duplicates, cycles, type safety, and deterministic ordering
- security coverage proves navigation inherits route-path protections
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-18 exit criteria

- [x] public immutable `Site` aggregate exists
- [x] site routes normalize to an immutable ordered tuple
- [x] duplicate canonical route paths fail explicitly
- [x] site exposes deterministic path and page projections
- [x] site provides canonical logical-route lookup
- [x] lookup input reuses LOT-16 route-path validation
- [x] optional site navigation is supported
- [x] navigation may reference a subset of site routes
- [x] navigation cannot reference routes absent from the site
- [x] navigation must reference the canonical Route objects owned by the site
- [x] public immutable `Sitemap` exists
- [x] public immutable `SitemapEntry` exists
- [x] sitemap contains all site routes regardless of navigation visibility
- [x] sitemap order follows site route declaration order
- [x] standalone sitemap rejects duplicate route paths
- [x] sitemap remains a domain model and does not serialize XML
- [x] site performs no rendering, filesystem, or build work

Next: **LOT-19 — Assets**.

## LOT-18 qualification evidence

- Site centralizes route identity and validates navigation consistency
- Sitemap is derived deterministically from the canonical site route set
- security coverage proves site lookup inherits route-path protections
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-19 exit criteria

- [x] public immutable `Asset` declaration exists
- [x] asset source is represented by `pathlib.Path`
- [x] asset target is represented by `PurePosixPath`
- [x] target is relative to the future output root
- [x] target traversal segments fail explicitly
- [x] target backslash/control/query/fragment ambiguity fails explicitly
- [x] encoded separators/traversal/control ambiguity fails explicitly
- [x] public path is derived deterministically from target
- [x] public immutable `Assets` collection exists
- [x] asset declaration order is preserved
- [x] duplicate publish targets fail explicitly
- [x] same source may be published to distinct targets
- [x] target lookup returns canonical Asset objects
- [x] source existence is not checked
- [x] no source files are read or copied
- [x] no filesystem output is performed

Next: **LOT-20 — Build Pipeline**.

## LOT-19 qualification evidence

- asset declarations are pure domain values with no I/O
- target validation protects the future output boundary before filesystem planning exists
- collection-level validation detects target collisions deterministically
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-20 exit criteria

- [x] public build-planning package exists
- [x] immutable `PageBuildEntry` exists
- [x] immutable `AssetBuildEntry` exists
- [x] immutable `BuildPlan` exists
- [x] public `BuildPlanner` exists
- [x] planner accepts canonical `Site` and optional `Assets`
- [x] root route maps to `index.html`
- [x] non-root routes map to pretty `<segments>/index.html` targets
- [x] page content is rendered into memory through the renderer contract
- [x] custom renderer injection is supported
- [x] asset entries retain canonical Asset declarations
- [x] page and asset target order is deterministic
- [x] exact target collisions fail explicitly
- [x] file/directory prefix collisions fail explicitly
- [x] page/page structural collisions fail explicitly
- [x] non-portable route-derived targets fail explicitly
- [x] collision validation happens before rendering
- [x] existing HTML escaping/security remains active during planning
- [x] no output root, mkdir, copy, write, or filesystem execution occurs

Next: **LOT-21 — Filesystem Output**.

## LOT-20 qualification evidence

- Site + Assets produce a deterministic complete in-memory BuildPlan
- route mapping and target safety are validated before materialization
- collisions are caught before renderer work or filesystem execution
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-21 exit criteria

- [x] public `FilesystemWriter` exists
- [x] public immutable `FilesystemWriteResult` exists
- [x] writer accepts only an already-qualified `BuildPlan`
- [x] caller supplies an explicit pathlib output root
- [x] missing output root is created deterministically
- [x] nested target directories are created as required
- [x] page content is written as UTF-8
- [x] asset bytes are copied from declared sources
- [x] existing targets fail by default
- [x] overwrite requires explicit `overwrite=True`
- [x] unplanned existing files remain untouched
- [x] predictable conflicts are preflighted before any write
- [x] missing asset sources fail before output-root creation
- [x] non-file asset sources fail explicitly
- [x] asset sources cannot overlap any planned output destination
- [x] output root symlinks fail explicitly
- [x] target-ancestor symlinks fail explicitly
- [x] target-file symlinks fail even with overwrite enabled
- [x] existing file/directory structural conflicts fail explicitly
- [x] default execution uses exclusive file creation
- [x] filesystem I/O failures are wrapped in build-specific errors
- [x] writer does not re-render or mutate the build plan
- [x] no global clean/delete behavior is introduced

Next: **LOT-22 — Static Site Generation**.

## LOT-21 qualification evidence

- a qualified BuildPlan now materializes into an actual static output tree
- predictable filesystem failures are rejected during preflight before writes begin
- symlink and overwrite protections enforce the output-root safety boundary
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-22 exit criteria

- [x] public `StaticSiteGenerator` exists
- [x] public immutable `StaticSiteGenerationResult` exists
- [x] generator accepts canonical `Site`
- [x] optional `Assets` are forwarded to planning
- [x] explicit output root is forwarded to filesystem output
- [x] overwrite policy is forwarded unchanged
- [x] planner and writer are independently injectable
- [x] planner remains responsible for rendering and target calculation
- [x] writer remains responsible for filesystem safety and materialization
- [x] planning failure prevents writer execution
- [x] existing build collision protection remains active
- [x] existing filesystem symlink protection remains active
- [x] generation result retains the exact `BuildPlan`
- [x] generation result retains the exact `FilesystemWriteResult`
- [x] result exposes output root and generated-file projections
- [x] complete Site + Assets generation works end-to-end
- [x] no new generic wrapper hides specific lower-level errors

Next: **LOT-23 — CLI Foundations**.

## LOT-22 qualification evidence

- the complete static generation path is now available through one explicit facade
- orchestration preserves the independently testable planner and writer layers
- lower-level planning and filesystem security invariants remain intact end-to-end
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-23 exit criteria

- [x] Typer is an explicit runtime dependency
- [x] Rich is an explicit runtime dependency
- [x] installed `pypagekit` console entry point exists
- [x] `python -m pypagekit` entry point exists
- [x] root Typer application is isolated under `pypagekit.cli`
- [x] centralized Rich stdout and stderr consoles exist
- [x] external values are not implicitly interpreted as Rich markup by the shared consoles
- [x] stable CLI exit-code constants define 0 / 1 / 2
- [x] `pypagekit --help` succeeds
- [x] `pypagekit -h` succeeds
- [x] bare invocation presents help successfully
- [x] `pypagekit --version` reports the canonical package version
- [x] unknown option returns usage exit code 2
- [x] unknown command returns usage exit code 2
- [x] unimplemented workflow commands are not advertised prematurely
- [x] command registration boundary exists for later LOTs
- [x] core domain/components/rendering/build packages do not import Typer or Rich
- [x] importing `pypagekit` does not load Typer or Rich
- [x] CliRunner coverage validates the root CLI contract
- [x] installed-wheel smoke validates console and module entry points

Next: **LOT-24 — Project Scaffolding**.

## LOT-23 qualification evidence

- the CLI boundary is installed and independently testable
- Typer and Rich remain isolated from the framework core
- shell and module entry points expose the same package version
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, package, and CLI-smoke gate


## LOT-24 exit criteria

- [x] public `pypagekit.project` package exists
- [x] immutable `ProjectFile` exists
- [x] immutable `ProjectPlan` exists
- [x] immutable `ProjectScaffoldResult` exists
- [x] public `ProjectScaffolder` exists
- [x] planning and filesystem materialization are separate operations
- [x] project planning creates no target files
- [x] project names normalize deterministically
- [x] scaffold contains .gitignore, README.md, pyproject.toml, and site.py
- [x] generated pyproject metadata is valid TOML
- [x] generated project declares a compatible PyPageKit 0.6.x dependency
- [x] generated site.py is immediately executable
- [x] generated site.py produces dist/index.html through StaticSiteGenerator
- [x] existing unplanned files are preserved
- [x] managed existing files fail by default
- [x] --force explicitly replaces managed regular files
- [x] target-root files fail explicitly
- [x] target-root and ancestor symlinks fail explicitly
- [x] managed target symlinks fail even with --force
- [x] pypagekit new TARGET is registered
- [x] pypagekit new . is supported
- [x] pypagekit new --help succeeds
- [x] missing CLI target remains usage exit code 2
- [x] scaffolding runtime failures become stderr + exit code 1
- [x] unimplemented build/serve/inspect/doctor commands remain unadvertised
- [x] project services remain independent from Typer and Rich

Next: **LOT-25 — Development Server**.

## LOT-24 qualification evidence

- project scaffolding works through both the Python service and Typer adapter
- the generated scaffold is valid and immediately executable
- preflight and symlink tests protect project creation boundaries
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, package, and CLI-smoke gate


## LOT-25 exit criteria

- [x] public pypagekit.development package exists
- [x] immutable DevelopmentServerConfig exists
- [x] immutable DevelopmentServerInfo exists
- [x] public DevelopmentServer service exists
- [x] explicit DevelopmentServerSession lifecycle exists
- [x] static root must already exist and be a directory
- [x] static root symlinks fail explicitly
- [x] static-root ancestor symlinks fail explicitly
- [x] host and port validation are explicit
- [x] Python API supports ephemeral port 0
- [x] CLI port range remains 1..65535
- [x] server never changes process cwd
- [x] root index.html is served
- [x] pretty nested directory index routes are served
- [x] binary assets are served
- [x] directory listing is disabled
- [x] development responses disable caching
- [x] missing resources return 404
- [x] encoded traversal cannot escape the root
- [x] encoded backslash ambiguity cannot escape the root
- [x] symlinked files/directories inside the root are not served
- [x] bind conflicts raise a framework-specific error
- [x] pypagekit serve is registered
- [x] serve defaults to dist / 127.0.0.1 / 8000
- [x] --host and --port are supported
- [x] runtime server failures become stderr + exit code 1
- [x] CLI validation failures remain usage exit code 2
- [x] generated project README documents pypagekit serve
- [x] no implicit build, watch, hot reload, or production-server behavior is introduced
- [x] development services remain independent from Typer and Rich

Next: **LOT-26 — Developer Diagnostics**.

## LOT-25 qualification evidence

- the static development server is independently usable from Python and the CLI
- actual HTTP tests cover pages, assets, cache headers, traversal and symlink boundaries
- CLI tests prove deterministic host/port/root delegation and exit-code behavior
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, package, and CLI-smoke gate


## LOT-26 exit criteria

- [x] public `pypagekit.diagnostics` package exists
- [x] immutable diagnostic result models exist
- [x] PASS / WARNING / FAIL statuses are explicit
- [x] diagnostic check ordering is deterministic
- [x] supported Python version is checked
- [x] installed PyPageKit version is reported
- [x] project root is checked without mutation
- [x] pyproject.toml presence is checked
- [x] project metadata is parsed read-only through stdlib tomllib
- [x] site.py presence is checked without importing or executing it
- [x] dist directory presence is checked
- [x] dist/index.html presence is checked
- [x] missing generated output remains a warning rather than a project-definition failure
- [x] symlinked diagnostic targets are not treated as trusted regular project files
- [x] public ProjectInspector exists
- [x] inspection reports project/package/output facts
- [x] malformed metadata is reported without executing project code
- [x] pypagekit doctor is registered
- [x] pypagekit inspect is registered
- [x] diagnostic failures use execution exit code 1
- [x] CLI usage failures remain exit code 2
- [x] services perform no filesystem writes
- [x] services perform no subprocess execution
- [x] services perform no network access
- [x] diagnostics services remain independent from Typer and Rich
- [x] installed-wheel smoke covers doctor and inspect help

Next: **0.7.x — Extensibility**.

## LOT-26 qualification evidence

- diagnostics and inspection are distinct read-only application services
- CLI adapters only present structured service results and translate exit status
- tests prove inspection does not execute site.py
- architecture tests enforce the Typer/Rich dependency boundary for diagnostics
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, package, and CLI-smoke gate


## Frozen remaining roadmap — LOT-27 to LOT-37

The remaining pre-1.0 roadmap is intentionally split into explicit implementation lots:

```text
0.7.x — Extensibility
LOT-27  Extension Contracts & Renderer Registry       0.7.0a1
LOT-28  Build & Component Extension Points            0.7.0a2
LOT-29  Plugin Discovery & Entry Points               0.7.0b1
LOT-30  Plugin Lifecycle & Conformance                0.7.0b2

0.8.x — Hardening
LOT-31  Security Hardening                            0.8.0a1
LOT-32  Reliability & Failure Hardening               0.8.0a2
LOT-33  Performance & Scalability Hardening           0.8.0b1

0.9.x — API Freeze
LOT-34  Public API Inventory & Stability Classification  0.9.0a1
LOT-35  Compatibility, Deprecation & Migration           0.9.0b1
LOT-36  1.0 Contract Freeze                              0.9.0rc1

1.0.0 — Stable
LOT-37  1.0 Release Qualification                    1.0.0
```

Roadmap rule:

```text
explicit extension contracts
        ↓
explicit extension points
        ↓
controlled discovery
        ↓
plugin conformance
        ↓
hardening
        ↓
public API classification
        ↓
compatibility / deprecation
        ↓
contract freeze
        ↓
1.0 qualification
```

No automatic plugin discovery is introduced before the explicit registries and extension contracts
have been exercised directly.


## LOT-27 exit criteria

- [x] public `pypagekit.extensions` package exists
- [x] immutable `ExtensionDescriptor` exists
- [x] extension IDs use a stable portable namespaced format
- [x] immutable `RendererExtension` contribution model exists
- [x] immutable `RendererRegistry` exists
- [x] registry ordering is deterministic
- [x] registration is persistent rather than mutating
- [x] duplicate extension IDs fail explicitly
- [x] unknown extension IDs fail explicitly
- [x] renderer factory output is validated before use
- [x] built-in HtmlRenderer is available through an explicit default registry
- [x] registered renderers integrate through existing BuildPlanner dependency injection
- [x] extensions package remains independent from Typer and Rich
- [x] no process-global mutable extension registry exists
- [x] no package discovery or dynamic import-string loading exists
- [x] no Python entry-point discovery exists yet
- [x] package version advances to `0.7.0a1`
- [x] GitHub CI qualification is fully green

Next after qualification: **LOT-28 — Build & Component Extension Points**.


## LOT-28 exit criteria

- [x] public `BuildPlannerProtocol` exists
- [x] `BuildPlanner` satisfies the structural planner contract
- [x] `StaticSiteGenerator` accepts structural planners without mandatory subclassing
- [x] invalid planner objects fail explicitly before generation
- [x] immutable `BuildPlannerExtension` exists
- [x] immutable `BuildPlannerRegistry` exists
- [x] build planner registration is deterministic and persistent
- [x] invalid build planner factory results fail explicitly
- [x] built-in build planner is exposed through an explicit default registry
- [x] immutable `ComponentExtension` exists
- [x] component contribution names reuse existing component-name validation
- [x] immutable `ComponentExtensionRegistry` exists
- [x] component extension ordering is deterministic
- [x] duplicate component names across extension bundles fail explicitly
- [x] component extensions materialize the existing `ComponentRegistry`
- [x] contributed components resolve through the existing `ComponentRuntime`
- [x] contributed component rendering preserves existing escaping/security behavior
- [x] built-in reusable components are exposed as an explicit extension bundle
- [x] no arbitrary mutable BuildPlan callback/hook is introduced
- [x] no process-global mutable extension registry exists
- [x] no package scanning, dynamic import-string loading, or entry-point discovery exists yet
- [x] extensions remain independent from Typer and Rich
- [x] package version advances to `0.7.0a2`
- [x] GitHub CI qualification is fully green

Next after qualification: **LOT-29 — Plugin Discovery & Entry Points**.


## LOT-29 exit criteria

- [x] public `EntryPointDiscovery` service exists
- [x] public immutable `PluginDiscoveryResult` exists
- [x] renderer entry-point group is fixed as `pypagekit.renderers`
- [x] build-planner entry-point group is fixed as `pypagekit.build_planners`
- [x] component entry-point group is fixed as `pypagekit.components`
- [x] discovery uses Python standard-library package metadata
- [x] constructing the discovery service performs no enumeration or plugin loading
- [x] plugin discovery occurs only through explicit `discover()`
- [x] entry points load zero-argument provider callables
- [x] renderer providers must return `RendererExtension`
- [x] build-planner providers must return `BuildPlannerExtension`
- [x] component providers must return `ComponentExtension`
- [x] entry-point names must be valid extension IDs
- [x] entry-point name must equal returned `descriptor.extension_id`
- [x] entry-point ordering is deterministic before provider execution
- [x] target import failures become framework-specific discovery errors
- [x] provider execution failures become framework-specific discovery errors
- [x] wrong provider return types fail explicitly
- [x] discovered extensions feed existing immutable registries
- [x] existing duplicate extension-ID protection remains active
- [x] existing duplicate component-contribution protection remains active
- [x] real dist-info metadata integration is covered
- [x] discovery performs no network access
- [x] no import-time discovery exists
- [x] no process-global mutable plugin registry exists
- [x] plugin lifecycle/activation/compatibility policy remains deferred to LOT-30
- [x] package version advances to `0.7.0b1`
- [x] GitHub CI qualification is fully green

Next after qualification: **LOT-30 — Plugin Lifecycle & Conformance**.


## LOT-30 exit criteria

- [x] public extension API compatibility identifier exists
- [x] extension descriptors can declare a major.minor PyPageKit extension API version
- [x] built-in extensions declare the current extension API
- [x] public immutable `PluginLifecycle` exists
- [x] public plugin kinds are explicit
- [x] public lifecycle states are explicit
- [x] initial lifecycle state is `DISCOVERED`
- [x] lifecycle transitions return new immutable values
- [x] qualification is an explicit operation
- [x] missing API compatibility declarations are rejected
- [x] incompatible extension API declarations are rejected
- [x] global extension-ID collisions across plugin kinds are rejected
- [x] renderer factory conformance is checked during qualification
- [x] build-planner factory conformance is checked during qualification
- [x] component bundles reuse existing structural registry validation
- [x] qualification failures isolate the invalid contribution
- [x] rejected plugins are excluded from qualified registries
- [x] activation requires prior qualification
- [x] rejected plugins cannot be activated
- [x] activation may target all or a selected subset of qualified plugins
- [x] active registries contain only active contributions
- [x] deactivation is explicit and immutable
- [x] deactivation does not unload modules or run third-party callbacks
- [x] no third-party activation/deactivation callback contract exists
- [x] no process-global mutable plugin registry exists
- [x] no hidden discovery or activation exists
- [x] installed entry-point plugin is covered end-to-end through activation
- [x] package version advances to `0.7.0b2`
- [x] GitHub CI qualification is fully green

After qualification, the `0.7.x — Extensibility` line is complete.

Next: **LOT-31 — Security Hardening** (`0.8.0a1`).


## LOT-31 exit criteria

- [x] output-root ancestor symlinks are rejected before directory creation
- [x] target symlinks remain rejected in overwrite mode
- [x] multiply-linked output files are rejected before overwrite
- [x] asset source/output identity conflicts include hard-link aliases
- [x] scaffold force mode rejects multiply-linked generated files
- [x] malformed URL percent escapes are rejected
- [x] percent-encoded ASCII controls are rejected
- [x] unsafe schemes hidden behind ASCII percent encoding are rejected
- [x] approved URL values remain unmodified
- [x] malformed development-server percent escapes fail closed
- [x] development-server DEL characters fail closed
- [x] development server emits no-store
- [x] development server emits nosniff
- [x] development server denies framing
- [x] development server emits a baseline self-only CSP
- [x] development server emits no-referrer policy
- [x] duplicate plugin entry-point names fail before provider loading
- [x] duplicate entry-point failure executes no duplicate providers
- [x] existing symlink traversal protections remain covered
- [x] existing HTML escaping and unsafe-scheme protections remain covered
- [x] package version advances to `0.8.0a1`
- [x] GitHub CI qualification is fully green

Next after qualification: **LOT-32 — Reliability & Failure Hardening** (`0.8.0a2`).


## LOT-32 exit criteria

- [x] build materialization tracks files mutated during one write operation
- [x] newly created build files are removed after a later write failure
- [x] partially copied assets are removed after failure
- [x] overwritten build files are restored after a later failure
- [x] transaction-created directories are removed when rollback leaves them empty
- [x] unplanned existing output files remain untouched by rollback
- [x] ordinary build materialization failures become `FilesystemWriteError`
- [x] original materialization exception remains available as cause
- [x] rollback failure becomes explicit `FilesystemRollbackError`
- [x] project scaffolding uses the same rollback semantics
- [x] newly scaffolded project trees are removed after failure
- [x] force-overwritten project files are restored after failure
- [x] project rollback failure has an explicit public error type
- [x] known PyPageKit renderer failures preserve their public exception type
- [x] unexpected renderer failures become `BuildRenderError`
- [x] unexpected renderer failure reports route context
- [x] original renderer exception remains available as cause
- [x] third-party planner output is validated before filesystem materialization
- [x] invalid planner output becomes `InvalidBuildPlanError`
- [x] renderer extension factory exceptions become `ExtensionFactoryError`
- [x] build-planner extension factory exceptions become `ExtensionFactoryError`
- [x] original extension factory exceptions remain available as cause
- [x] plugin lifecycle conformance remains fault-isolating with factory failures
- [x] package version advances to `0.8.0a2`
- [x] GitHub CI qualification is fully green

Next after qualification: **LOT-33 — Performance & Scalability Hardening** (`0.8.0b1`).


## LOT-33 exit criteria

- [x] build target collision validation no longer uses pairwise target scanning
- [x] collision validation scales with total target path depth
- [x] exact duplicate target detection remains explicit
- [x] file/directory collision detection remains explicit in both declaration orders
- [x] deterministic collision error behavior is preserved
- [x] Site route membership and lookup use immutable logarithmic indexes
- [x] Assets target membership and lookup use immutable logarithmic indexes
- [x] ComponentRegistry caches names and performs logarithmic lookup
- [x] build-planner extension registry caches IDs and performs logarithmic lookup
- [x] component extension registry caches IDs and contributed names
- [x] renderer extension registry caches IDs and performs logarithmic lookup
- [x] public immutable declaration ordering remains unchanged
- [x] private lookup indexes do not affect public equality/repr semantics
- [x] asset/output inode conflict detection avoids assets × destinations scans
- [x] hard-link security behavior remains covered
- [x] overwrite rollback snapshot avoids full-file backup copy
- [x] overwrite rollback semantics remain covered
- [x] component runtime allocates replacement children only after an actual resolution change
- [x] duplicate entry-point detection is linear after sorting
- [x] duplicate entry points still fail before provider loading
- [x] large build-target collection is covered without timing assertions
- [x] large Site/Assets/registry lookup collections are covered without timing assertions
- [x] package version advances to `0.8.0b1`
- [x] GitHub CI qualification is fully green

After qualification, the `0.8.x — Hardening` line is complete.

Next: **LOT-34 — Public API Inventory & Stability Classification** (`0.9.0a1`).


## LOT-34 exit criteria

- [x] canonical human-readable public API document exists
- [x] machine-readable public API inventory exists
- [x] stable-candidate classification is defined
- [x] provisional-public classification is defined
- [x] operational-contract classification is defined
- [x] internal classification is defined
- [x] root `pypagekit` facade is inventoried exactly
- [x] `pypagekit.domain` facade is inventoried exactly
- [x] `pypagekit.components` facade is inventoried exactly
- [x] `pypagekit.rendering` facade is inventoried exactly
- [x] `pypagekit.build` facade is inventoried exactly
- [x] `pypagekit.project` facade is inventoried exactly
- [x] `pypagekit.development` facade is inventoried exactly
- [x] `pypagekit.diagnostics` facade is inventoried exactly
- [x] `pypagekit.extensions` facade is inventoried exactly
- [x] `pypagekit.exceptions` facade is inventoried exactly
- [x] Python-level CLI facade is classified provisional-public
- [x] shell CLI command names are inventoried
- [x] shell CLI exit semantics are inventoried
- [x] Python plugin entry-point group names are inventoried
- [x] built-in extension IDs are inventoried
- [x] extension compatibility version is inventoried
- [x] PEP 561 typing marker is inventoried
- [x] minimum supported Python version is inventoried
- [x] deep-import/internal-module policy is explicit
- [x] CI verifies facade `__all__` values against the inventory
- [x] CI verifies operational constants against runtime/package metadata
- [x] package version advances to `0.9.0a1`
- [x] GitHub CI qualification is fully green

Next after qualification: **LOT-35 — Compatibility, Deprecation & Migration** (`0.9.0b1`).


## LOT-35 exit criteria

- [x] canonical compatibility policy exists
- [x] machine-readable compatibility policy exists
- [x] canonical 0.9.x → 1.0 migration guide exists
- [x] machine-readable deprecation registry exists
- [x] stable-candidate compatible changes are classified
- [x] stable-candidate breaking changes are classified
- [x] provisional-public evolution rules are explicit
- [x] operational-contract evolution rules are explicit
- [x] post-1.0 semantic-versioning policy is explicit
- [x] silent stable-API removal is forbidden
- [x] future public deprecations require structured metadata
- [x] standard `DeprecationWarning` is the canonical warning category
- [x] internal warning helper emits deterministic migration context
- [x] post-1.0 deprecations remain supported through the current major line
- [x] compatibility aliases are preferred for public renames/moves
- [x] CLI compatibility rules cover commands/options/exit semantics
- [x] plugin compatibility rules cover entry-point groups and extension API line
- [x] exception hierarchy compatibility is documented
- [x] typing compatibility is documented
- [x] security exception to deprecation timing is narrowly defined
- [x] active public deprecation registry is empty at 0.9.0b1
- [x] architecture tests validate compatibility artifact versions
- [x] architecture tests validate future deprecation records
- [x] migration guide directs users away from deep imports
- [x] migration guide enables deprecation warnings in CI
- [x] migration guide covers plugin authors
- [x] package version advances to `0.9.0b1`
- [x] GitHub CI qualification is fully green

Next after qualification: **LOT-36 — 1.0 Contract Freeze** (`0.9.0rc1`).


## LOT-36 exit criteria

- [x] package version advances to `0.9.0rc1`
- [x] accepted stable-candidate facades are promoted to `stable`
- [x] exact machine-readable 1.0 baseline exists
- [x] human-readable 1.0 contract document exists
- [x] stable facade export names are frozen
- [x] public function signatures are frozen
- [x] public constructor signatures are frozen
- [x] public class and protocol members are frozen
- [x] public class inheritance relationships are frozen
- [x] public dataclass fields and semantic configuration are frozen
- [x] private dataclass fields are excluded from the public baseline
- [x] public exception hierarchy is frozen
- [x] enum member names and values are frozen
- [x] public type aliases are frozen
- [x] public constants are frozen
- [x] shell CLI invocation forms are frozen
- [x] shell CLI command names are frozen
- [x] CLI root options are frozen
- [x] CLI exit-code semantics are frozen
- [x] Python/Typer CLI facade remains explicitly provisional
- [x] extension entry-point groups are frozen
- [x] built-in extension IDs are frozen
- [x] extension API `0.7` is deliberately retained
- [x] PEP 561 typing marker is frozen
- [x] minimum Python 3.11 is frozen
- [x] active deprecation set is empty at freeze
- [x] contract snapshot ignores physical internal module layout
- [x] version symbol is not pinned to release-candidate value
- [x] standard-library runtime representation differences are normalized
- [x] exact contract baseline passes Python 3.11
- [x] exact contract baseline passes Python 3.12
- [x] exact contract baseline passes Python 3.13
- [x] exact contract baseline passes Python 3.14
- [x] GitHub CI qualification is fully green on the final documentation head

Next after qualification: **LOT-37 — 1.0 Release Qualification** (`1.0.0`).


## LOT-37 exit criteria

- [x] package version advances to `1.0.0`
- [x] distribution classifier advances to Production/Stable
- [x] public API, compatibility, and deprecation metadata track `1.0.0`
- [x] generated project requirement advances to `pypagekit>=1.0.0,<1.1`
- [x] exact LOT-36 contract file identity is pinned by Git blob SHA
- [x] runtime-to-baseline exact contract gate remains active
- [x] extension compatibility API remains `0.7`
- [x] Python/Typer CLI facade remains provisional
- [x] active public deprecation registry remains empty
- [x] release qualification document exists
- [x] CI qualifies Python 3.11
- [x] CI qualifies Python 3.12
- [x] CI qualifies Python 3.13
- [x] CI qualifies Python 3.14
- [x] CI builds sdist and wheel
- [x] CI installs and validates wheel metadata
- [x] CI validates installed PEP 561 `py.typed`
- [x] CI runs `pip check`
- [x] CI smoke-tests installed shell and module CLI entry points
- [x] CI scaffolds and executes a real generated project
- [x] CI installs and smoke-tests the sdist in a fresh virtual environment
- [ ] GitHub pull-request CI is fully green
- [ ] LOT-37 is merged to `main`
- [ ] final `main` CI is fully green

LOT-37 is a qualification lot, not a feature lot. Any stable contract drift requires reopening the
LOT-36 freeze rather than silently refreshing the baseline.
