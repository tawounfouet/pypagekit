# PyPageKit

PyPageKit is a Python-first framework for describing pages as structured Python objects, composing reusable components, rendering safe HTML, and progressively building static sites.

## Status

**PyPageKit 1.0.0 remains the qualified stable baseline.** Development is now on `1.1.0b2` with LOT-42 — Serve Watch Mode & Live Reload. The frozen `API_CONTRACT_1_0.json` remains the backward-compatibility floor.

PyPageKit can now perform its first complete in-memory transformation:

```text
Page / Component
      ↓
ComponentRuntime
      ↓
Resolved Content Tree
      ↓
HtmlRenderer
      ↓
HTML5 str
```

Implemented so far:

- typed `src/` package and CI foundations;
- immutable structured page/content domain;
- deterministic HTML5 serialization;
- context-specific text and attribute escaping;
- public `Renderer` protocol;
- public `HtmlRenderer`;
- recursive rendering for the complete current domain tree;
- compact complete HTML5 document output for `Page`;
- render-time URL safety validation for links and images;
- adversarial XSS coverage for text, attributes, nested composition, and unsafe schemes;
- deterministic page metadata rendering for title, language, charset, and description;
- reusable component abstraction with explicit runtime resolution;
- named structural layouts and regions without CSS assumptions;
- built-in reusable components composed entirely from the existing domain primitives;
- named slot composition with wrapperless multi-node injection;
- explicit immutable component registry and symbolic component references;
- canonical logical routes that bind URL paths to pages;
- immutable hierarchical navigation that references those routes directly;
- a canonical Site aggregate with deterministic Sitemap projection;
- declarative static assets with validated publish targets and no filesystem I/O;
- deterministic in-memory build planning for pages and assets;
- deterministic SHA-256 build fingerprints and immutable build manifests;
- drift-safe incremental build diffs and minimal filesystem materialization;
- explicit deterministic filesystem snapshots and debounced change batches;
- opt-in `serve --watch` orchestration with incremental rebuilds and browser live reload;
- safe filesystem materialization of qualified build plans;
- end-to-end static-site generation through a thin orchestration facade;
- Typer + Rich CLI foundations with installed shell and module entry points;
- safe project scaffolding through `pypagekit new`;
- local static development serving through `pypagekit serve`;
- read-only developer diagnostics through `pypagekit doctor` and `pypagekit inspect`;
- explicit renderer extension contracts and immutable registration through `pypagekit.extensions`;
- structural build-planner extensions and component-extension bundles;
- explicit installed-plugin discovery through Python entry points;
- explicit plugin compatibility, qualification, activation, and deactivation lifecycle.

## Quick example

```python
from pypagekit import Attributes, Container, Heading, Image, Link, Page, Paragraph
from pypagekit.rendering import HtmlRenderer


page = Page(
    title="Home & Docs",
    lang="en",
    description="A Python-first structured page.",
    content=[
        Container(
            children=[
                Heading(
                    "Welcome",
                    level=1,
                    attributes=Attributes(id="hero-title", classes=["display"]),
                ),
                Paragraph("Built with structured Python objects."),
                Link(label="About", href="/about"),
                Image(src="/assets/logo.png", alt="Project logo"),
            ]
        )
    ],
)

html = HtmlRenderer().render(page)
print(html)
```

The result is a deterministic HTML5 document containing the doctype, language, UTF-8 charset, title, optional description metadata, body, and recursively rendered content.

## Rendering architecture

```text
Domain object
     ↓
HtmlRenderer
     ↓
escaping
     ↓
HTML serializer
     ↓
str
```

The domain remains unaware of HTML:

```python
Heading("A & B")
```

is stored exactly as authored. During rendering it becomes:

```html
<h1>A &amp; B</h1>
```

## Current HTML mappings

```text
Text       → escaped text
Heading    → h1..h6
Paragraph  → p
Container  → div
Link       → a
Image      → img
Page       → complete HTML5 document
```

## Safe-by-default rendering

PyPageKit now validates URL references before they reach HTML attribute serialization.

Allowed link forms include:

```text
/about
#section
?q=python
https://example.com
http://example.com
mailto:hello@example.com
```

Image sources support relative references plus `http` and `https`.

Active or local-resource schemes such as `javascript:`, `data:`, `vbscript:`, and `file:` are rejected with `UnsafeUrlError`.

Text remains escaped at the HTML boundary and the core exposes no raw-HTML escape hatch.

## Deliberate boundaries

LOT-08 does not yet introduce:

- filesystem output — later build/output LOTs.

## Requirements

- Python 3.11+

## Build fingerprints and manifests

LOT-39 adds content identity without changing materialization:

```python
from pypagekit.build import BuildPlanner, build_manifest

plan = BuildPlanner().plan(site, assets)
manifest = build_manifest(plan)

for entry in manifest:
    print(entry.target, entry.kind, entry.fingerprint)
```

The contract is intentionally content-based:

```text
page content
    ↓ UTF-8
SHA-256

asset source
    ↓ streamed bytes
SHA-256
```

Targets and timestamps are not part of the fingerprint. The target lives in the manifest entry;
LOT-40 can therefore compare the same target across two manifests and decide whether its content
actually changed.

`build_manifest()` may read declared asset files when explicitly called, but it performs no output
writes and starts no watcher or background service.

## Incremental builds

LOT-40 turns manifests into an explicit transition:

```python
from pypagekit.build import StaticSiteGenerator, build_manifest

generator = StaticSiteGenerator()

first = generator.generate(site, output_root, assets=assets)
previous = build_manifest(first.plan)

second = generator.generate_incremental(
    updated_site,
    previous,
    output_root,
    assets=updated_assets,
)

print(second.diff.added_targets)
print(second.diff.changed_targets)
print(second.diff.unchanged_targets)
print(second.diff.removed_targets)
```

The filesystem contract is conservative:

```text
previous manifest
       +
actual output verification
       +
next manifest
       ↓
added / changed / unchanged / removed
       ↓
single rollback-capable transaction
```

PyPageKit verifies every previously tracked output before mutation. A manual edit or missing tracked
file raises `IncrementalOutputDriftError` rather than being silently overwritten.

Only added and changed files are written; removed files are transactionally deleted; unchanged files
are left untouched. Unplanned output files remain outside the transition. Empty directories are not
pruned by LOT-40.

## Filesystem watching

LOT-41 adds a development watcher without coupling it to the HTTP server:

```python
from pathlib import Path, PurePosixPath

from pypagekit.development import DevelopmentWatcher

watcher = DevelopmentWatcher(
    Path("."),
    ignored_paths=(PurePosixPath("dist"),),
)

snapshot = watcher.snapshot()

batch = watcher.wait_for_changes(
    snapshot,
    poll_interval=0.1,
    debounce_interval=0.05,
)

if batch is not None:
    print(batch.created)
    print(batch.modified)
    print(batch.deleted)
```

The loop remains explicit:

```text
snapshot()
   ↓
wait_for_changes(previous)
   ↓
WatchChangeBatch
   ↓
application decides what happens next
```

LOT-41 does **not** rebuild a project and does **not** start the development server. That integration
belongs to LOT-42.

Symlinks are observed as symlinks and are never followed. Regular files are content-hashed, so a
same-size edit is still detected even when metadata alone would be ambiguous.

## Serve with watch + live reload

The normal development server remains unchanged:

```bash
pypagekit serve
```

Opt into the integrated development loop with:

```bash
pypagekit serve --watch
```

The default watch contract expects the current project to expose a module-level `site` from
`site.py`. A module-level `assets` value may also be provided.

```text
site.py / local project sources
            ↓
DevelopmentWatcher
            ↓
debounced WatchChangeBatch
            ↓
fresh Python subprocess
            ↓
BuildPlan
            ↓
LOT-40 incremental materialization
            ↓
successful commit
            ↓
DevelopmentServerSession.notify_reload()
            ↓
browser reload
```

The fresh subprocess avoids stale imported local modules between rebuilds. Generated `dist/` output
is excluded from the watcher, so the rebuild cannot trigger itself.

Useful tuning options:

```bash
pypagekit serve --watch \
  --entry site.py \
  --poll-interval 0.10 \
  --debounce-interval 0.05
```

A failed project import, render, or incremental write keeps the last successful output online and
does not notify browsers.

Live reload is development-only. PyPageKit injects an external same-origin reload script into HTTP
responses without modifying generated HTML files on disk and without enabling inline scripts in the
development CSP.

## Post-1.0 roadmap

The first compatible minor train is defined in [ROADMAP_1_X.md](ROADMAP_1_X.md):

```text
LOT-38  compatibility baseline gate
LOT-39  build fingerprints + manifest
LOT-40  incremental build diff/materialization
LOT-41  watch service
LOT-42  serve --watch + live reload
LOT-43  1.1 RC contract snapshot
LOT-44  1.1 release qualification
```

The frozen 1.0 contract remains the compatibility floor for every 1.1 LOT.

## Release and publication

The stable package release process is documented in [RELEASING.md](RELEASING.md).

Publication is intentionally separated from release qualification:

```text
qualified main
    ↓
vX.Y.Z tag
    ↓
GitHub Release
    ↓
PyPI Trusted Publishing
```

The publication workflow never changes the frozen 1.0 compatibility baseline.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"

ruff check .
ruff format --check .
mypy
pytest
python -m build
```

## Roadmap

```text
0.1.x  Domain                  ✅ feature-complete
0.2.x  Rendering               ✅ feature-complete
0.3.x  Components              ✅ feature-complete
0.4.x  Routing & Site           ✅ feature-complete
0.5.x  Static Build              ✅ feature-complete
0.6.x  CLI & Developer Workflow   ✅ feature-complete
0.7.x  Extensibility               ✅ feature-complete
0.8.x  Hardening                    ✅ feature-complete
0.9.x  API Freeze                   ✅ contract frozen
1.0.0  Stable                       ✅ qualified
```

The **`0.9.x — API Freeze`** line and **LOT-37 — 1.0 Release Qualification** are complete. The historical LOT-01 → LOT-37 implementation train is closed at `1.0.0`. See `RELEASE_1_0.md`.


## Controlled attributes

HTML-backed content may use a typed `Attributes` value object:

```python
attributes = Attributes(
    id="hero",
    classes=["section", "wide"],
    title="Hero section",
    data={"testid": "hero"},
    aria={"label": "Hero"},
)
```

This renders only the controlled hooks `id`, `class`, `title`, `data-*`, and `aria-*`. Inline style and event-handler keywords are intentionally not part of the API.

With LOT-10 complete, the `0.2.x` rendering line is feature-complete and the next major layer is reusable components.


## Components

Components compose ordinary PyPageKit content without producing HTML directly:

```python
from dataclasses import dataclass

from pypagekit import Component, Container, Content, Heading, Paragraph


@dataclass(frozen=True, slots=True)
class Hero(Component):
    title: str
    body: str

    def compose(self) -> Content:
        return Container(
            [
                Heading(self.title),
                Paragraph(self.body),
            ]
        )
```

They can be placed directly inside a page:

```python
page = Page(
    title="Components",
    content=[Hero("Welcome", "Hello")],
)
```

Rendering follows:

```text
Component
   ↓ compose()
Content Tree
   ↓
ComponentRuntime
   ↓
HtmlRenderer
   ↓
HTML
```

`ComponentRuntime` validates composition results, resolves nested components, detects active-object cycles, and enforces a configurable nesting-depth guard.


## Layouts

Layouts are specialized components that declare ordered structural regions:

```python
from dataclasses import dataclass

from pypagekit import Layout, LayoutRegion, Paragraph


@dataclass(frozen=True, slots=True)
class AppLayout(Layout):
    def regions(self) -> tuple[LayoutRegion, ...]:
        return (
            LayoutRegion("header", [Paragraph("Header")]),
            LayoutRegion("main", [Paragraph("Body")]),
            LayoutRegion("footer", [Paragraph("Footer")]),
        )
```

The layout does not choose CSS or grid behavior. It composes into ordinary content, and the HTML renderer currently represents each region neutrally:

```html
<div data-layout-region="header">...</div>
<div data-layout-region="main">...</div>
<div data-layout-region="footer">...</div>
```

This keeps the responsibility split explicit:

```text
Layout
  ↓ regions()
Structural Regions
  ↓
ComponentRuntime
  ↓
Resolved Content
  ↓
HtmlRenderer
```

Layouts may now declare and bind named slots while remaining structurally renderer-independent.


## Built-in reusable components

LOT-13 introduces a deliberately small catalogue under `pypagekit.components`:

```python
from pypagekit import Paragraph
from pypagekit.components import Card, Hero, Section


hero = Hero(
    "Welcome",
    body="Build pages from structured Python objects.",
)

section = Section(
    "Overview",
    [
        Paragraph("First block."),
        Card(
            [Paragraph("Reusable content.")],
            title="Card title",
        ),
    ],
)
```

The built-ins remain ordinary components:

```text
Section / Card / Hero
        ↓ compose()
core Content primitives
        ↓
ComponentRuntime
        ↓
HtmlRenderer
```

They add no implicit CSS classes, hidden data markers, event handlers, or alternate renderer behavior. Styling remains opt-in through the existing `Attributes` model.

Named slots are now available through LOT-14.


## Slots and wrapperless composition

LOT-14 adds explicit named injection points:

```python
from dataclasses import dataclass

from pypagekit import (
    Content,
    Fragment,
    Paragraph,
    Slot,
    SlotBindings,
    SlottedComponent,
)


@dataclass(frozen=True, slots=True)
class Shell(SlottedComponent):
    bindings: SlotBindings

    def template(self) -> Content:
        return Fragment(
            [
                Paragraph("Before"),
                Slot("body", required=True),
                Paragraph("After"),
            ]
        )

    def slot_bindings(self) -> SlotBindings:
        return self.bindings
```

Usage:

```python
shell = Shell(
    SlotBindings(
        {
            "body": [
                Paragraph("One"),
                Paragraph("Two"),
            ]
        }
    )
)
```

The slot may inject several nodes without creating an artificial wrapper:

```text
Slot("body")
    ↓ binding
Paragraph("One")
Paragraph("Two")
    ↓
Fragment
    ↓
ComponentRuntime
    ↓
HtmlRenderer
    ↓
<p>One</p><p>Two</p>
```

A missing optional slot uses its fallback, while a required slot must be explicitly bound. An explicit empty binding is valid and intentionally produces no content.

Bindings are lexical: a component or layout resolves only the slots declared in its own template. Global component registration remains the concern of LOT-15.


## Explicit component registry

LOT-15 adds symbolic component references without introducing global mutable state:

```python
from dataclasses import dataclass

from pypagekit import Component, ComponentRef, Content, Paragraph
from pypagekit.components import ComponentRegistry, ComponentRuntime
from pypagekit.rendering import HtmlRenderer


@dataclass(frozen=True, slots=True)
class Message(Component):
    text: str

    def compose(self) -> Content:
        return Paragraph(self.text)


registry = ComponentRegistry({"message": Message})
runtime = ComponentRuntime(registry=registry)
renderer = HtmlRenderer(component_runtime=runtime)

html = renderer.render(ComponentRef("message", {"text": "Hello"}))
```

Registration is persistent rather than mutating:

```python
base = ComponentRegistry()
extended = base.register("message", Message)

assert base.names == ()
assert extended.names == ("message",)
```

The registry performs no dynamic imports and no implicit discovery:

```text
ComponentRef
    ↓
explicit ComponentRegistry
    ↓ factory
Component
    ↓
ComponentRuntime
    ↓
Content
    ↓
HtmlRenderer
```

With LOT-15 complete, the component layer is closed and the roadmap moves to routing and site composition.


## Logical routes

LOT-16 separates a page from its logical site location:

```python
from pypagekit import Page, Paragraph, Route


about_page = Page(
    title="About",
    content=[Paragraph("About this project.")],
)

route = Route("/about", about_page)
```

The key boundary is:

```text
Page
  ≠
Route
  ≠
Filesystem output path
```

Routes are canonical logical URL paths. For example:

```python
Route("/", page).path  # "/"
Route("/about/", page).path  # "/about"
Route("/docs/api", page).segments
# ("docs", "api")
```

A route cannot contain a query string, fragment, external URL, protocol-relative URL, empty internal segment, traversal segment, backslash separator, or ambiguous encoded separator.

LOT-16 deliberately does not map routes to `index.html` files yet. Physical output planning belongs to the later build pipeline.


## Navigation

LOT-17 builds hierarchical navigation directly from route objects:

```python
from pypagekit import Navigation, NavigationItem, Page, Route


docs = Route("/docs", Page("Docs"))
api = Route("/docs/api", Page("API"))
about = Route("/about", Page("About"))

navigation = Navigation(
    [
        NavigationItem(
            "Docs",
            docs,
            [
                NavigationItem("API", api),
            ],
        ),
        NavigationItem("About", about),
    ]
)
```

Navigation does not copy URL strings:

```text
Page
  ↓
Route
  ↑
NavigationItem
  ↓
Navigation
```

The tree is immutable and ordered. A route path may appear only once in one navigation tree, cycles are rejected, and traversal is deterministic:

```python
navigation.route_paths
# ("/docs", "/docs/api", "/about")
```

Labels remain semantic strings. Navigation does not render HTML and does not decide which item is active. Site-wide consistency between routes, navigation, and sitemap belongs to LOT-18.


## Site and sitemap

LOT-18 introduces the aggregate that owns canonical site routes:

```python
from pypagekit import (
    Navigation,
    NavigationItem,
    Page,
    Route,
    Site,
)


home = Route("/", Page("Home"))
docs = Route("/docs", Page("Docs"))
hidden = Route("/hidden", Page("Hidden"))

navigation = Navigation(
    [
        NavigationItem("Home", home),
        NavigationItem("Docs", docs),
    ]
)

site = Site(
    [home, docs, hidden],
    navigation=navigation,
)
```

The site is now the consistency boundary:

```text
Site
├── Routes      ← canonical route objects
├── Navigation  ← references site routes
└── Sitemap     ← derived from all site routes
```

Navigation may intentionally omit routes while the sitemap still covers them:

```python
site.paths
# ("/", "/docs", "/hidden")

site.navigation.route_paths
# ("/", "/docs")

site.sitemap.paths
# ("/", "/docs", "/hidden")
```

Logical lookup stays independent from filesystem output:

```python
site.route("/docs/") is docs
# True
```

`Sitemap` is currently a pure domain projection. XML serialization, build paths, and file output remain later build concerns.


## Assets

LOT-19 describes publishable static resources without touching the filesystem:

```python
from pathlib import Path, PurePosixPath

from pypagekit import Asset, Assets


logo = Asset(
    source=Path("static/logo.png"),
    target=PurePosixPath("assets/logo.png"),
)

assets = Assets([logo])
```

The model deliberately separates local source location from public target:

```text
Path("static/logo.png")
        ↓
      Asset
        ↓
PurePosixPath("assets/logo.png")
        ↓
public_path == "/assets/logo.png"
```

The source does not need to exist when the declaration is created. LOT-19 performs no `open()`, `stat()`, copy, mkdir, hash, or write operation.

Asset targets are validated before they can enter future build planning. They must remain relative, POSIX-style, traversal-free, and unambiguous. `Assets` also rejects duplicate targets:

```python
assets.targets
# (PurePosixPath("assets/logo.png"),)

assets.public_paths
# ("/assets/logo.png",)
```

LOT-20 will consume `Site` + `Assets` to produce a build plan. Physical file operations remain deferred to LOT-21.


## Build planning

LOT-20 combines logical site structure and declarative assets into a complete in-memory build plan:

```python
from pathlib import Path, PurePosixPath

from pypagekit import Asset, Assets, Page, Route, Site
from pypagekit.build import BuildPlanner


site = Site(
    [
        Route("/", Page("Home")),
        Route("/about", Page("About")),
    ]
)

assets = Assets(
    [
        Asset(
            Path("static/logo.svg"),
            PurePosixPath("assets/logo.svg"),
        )
    ]
)

plan = BuildPlanner().plan(site, assets)
```

Route mapping is deterministic and filesystem-independent:

```text
/          -> index.html
/about     -> about/index.html
/docs/api  -> docs/api/index.html
```

The planner produces:

```text
Site ------------------┐
                       │
                       v
                  BuildPlanner
                       │
Assets ----------------┘
                       │
                       v
                    BuildPlan
              ┌────────┴────────┐
              v                 v
      PageBuildEntry[]   AssetBuildEntry[]
      target + HTML      source + target
```

The HTML is already rendered into memory, but no output directory or file is created. Target collisions are validated before rendering, including exact collisions and file/directory conflicts.

For example, these plans are rejected before any write occurs:

```text
page  -> index.html
asset -> index.html                 collision

page  -> docs/index.html
asset -> docs                       file/directory collision

page  -> docs/index.html
page  -> docs/index.html/index.html file/directory collision
```

LOT-21 will execute an already-qualified `BuildPlan` against an explicit output root.


## Filesystem output

LOT-21 materializes an existing `BuildPlan` under an explicit output root:

```python
from pathlib import Path

from pypagekit.build import FilesystemWriter


result = FilesystemWriter().write(
    plan,
    Path("dist"),
)
```

The responsibility split is now explicit:

```text
Site + Assets
      ↓
BuildPlanner
      ↓
BuildPlan
      ↓
FilesystemWriter
      ↓
dist/
├── index.html
├── about/
│   └── index.html
└── assets/
    └── logo.svg
```

The writer does not render pages and does not derive targets. It executes the already-qualified plan.

By default, existing targets are protected:

```python
FilesystemWriter().write(plan, Path("dist"))
# raises ExistingOutputError if a planned file already exists
```

Replacement must be explicit:

```python
FilesystemWriter().write(
    plan,
    Path("dist"),
    overwrite=True,
)
```

Even with overwrite enabled, output-root symlinks, symlinked target ancestors, and target-file symlinks are rejected. Missing or invalid asset sources are also detected during preflight before predictable writes begin.

Unplanned files are intentionally preserved; LOT-21 does not implement a global clean operation.

The result records exactly what was materialized:

```python
result.page_files
result.asset_files
result.files
```

LOT-22 will provide the first end-to-end static-site generation facade that plans and writes a `Site` in one controlled workflow.


## Static site generation

LOT-22 provides the high-level facade that joins the existing build layers:

```python
from pathlib import Path

from pypagekit.build import StaticSiteGenerator


result = StaticSiteGenerator().generate(
    site,
    Path("dist"),
    assets=assets,
)
```

The architecture remains layered:

```text
Site + Assets
      ↓
StaticSiteGenerator
      ↓
BuildPlanner
      ↓
BuildPlan
      ↓
FilesystemWriter
      ↓
StaticSiteGenerationResult
      ↓
dist/
```

The generator does not duplicate planner or writer behavior. It simply coordinates them.

The result retains both forms of evidence:

```python
result.plan
result.write_result

result.output_root
result.page_files
result.asset_files
result.files
```

Overwrite behavior remains explicit:

```python
StaticSiteGenerator().generate(
    site,
    Path("dist"),
    assets=assets,
    overwrite=True,
)
```

Build collisions, unsafe targets, invalid asset sources, existing-output policy, and symlink protections continue to raise their existing specific exceptions.

With LOT-22 complete, PyPageKit now supports the full programmatic static-site lifecycle:

```text
Python objects
      ↓
Page / Component
      ↓
Route / Site
      ↓
Assets
      ↓
BuildPlan
      ↓
Filesystem output
      ↓
Static site
```

The next release line, `0.6.x`, adds developer workflow and CLI surfaces on top of this stable programmatic pipeline.


## CLI foundations

LOT-23 introduces the official PyPageKit command-line boundary using Typer + Rich:

```bash
pypagekit --help
pypagekit --version

python -m pypagekit --help
python -m pypagekit --version
```

The responsibility split is explicit:

```text
Typer
  ↓
CLI parsing / dispatch

PyPageKit Core
  ↓
execution semantics

Rich
  ↓
human terminal presentation
```

The shared Rich consoles disable markup and automatic highlighting by default so project values are treated as literal text unless presentation code explicitly opts into richer formatting.

LOT-23 intentionally does not advertise workflow commands that are not implemented yet. The registration boundary is ready, and subsequent lots add commands only when their underlying workflow exists:

```text
LOT-24  pypagekit new
LOT-25  pypagekit serve
LOT-26  pypagekit inspect / doctor
```

The CLI layer remains optional from the core's architectural perspective: importing `pypagekit` does not import Typer or Rich, and domain/components/rendering/build packages are forbidden from depending on them.


## Project scaffolding

LOT-24 adds the first workflow command:

```bash
pypagekit new my-site
```

It creates a minimal executable project:

```text
my-site/
├── .gitignore
├── README.md
├── pyproject.toml
└── site.py
```

The generated project can immediately be executed:

```bash
cd my-site
python site.py
```

which produces:

```text
dist/
└── index.html
```

The CLI remains a thin adapter:

```text
pypagekit new
      ↓
Typer command
      ↓
ProjectScaffolder
      ↓
ProjectPlan
      ↓
filesystem materialization
```

Existing scaffold-managed files are protected by default. Replacement must be explicit:

```bash
pypagekit new my-site --force
```

`--force` never permits replacing or traversing symlinks. Unplanned files in an existing target directory are preserved.

The underlying service is also directly usable from Python:

```python
from pathlib import Path
from pypagekit.project import ProjectScaffolder

result = ProjectScaffolder().scaffold(Path("my-site"))
```

LOT-24 deliberately does not add project loading or a CLI build command. The generated `site.py` uses the already-qualified Python generation API directly.


## Development server

LOT-25 adds a local static preview server:

```bash
python site.py
pypagekit serve
```

By default it serves:

```text
root  = dist/
host  = 127.0.0.1
port  = 8000
```

Custom values are explicit:

```bash
pypagekit serve public --host 0.0.0.0 --port 9000
```

The architecture remains separated:

```text
pypagekit serve
      ↓
Typer adapter
      ↓
DevelopmentServerConfig
      ↓
DevelopmentServer
      ↓
stdlib ThreadingHTTPServer
      ↓
generated static output
```

The service is also available directly from Python:

```python
from pathlib import Path
from pypagekit.development import DevelopmentServer, DevelopmentServerConfig

config = DevelopmentServerConfig(
    Path("dist"),
    host="127.0.0.1",
    port=8000,
)

DevelopmentServer().serve(config)
```

LOT-25 intentionally does not build the site automatically. It serves an already-generated directory. This keeps project execution/build semantics separate from HTTP serving.

Development safety rules include:

```text
directory listing          disabled
browser cache              no-store
root symlink               rejected
root-ancestor symlink      rejected
requested symlink path     rejected
encoded traversal          confined / rejected
process cwd mutation       none
```

This server is a development convenience, not a production HTTP server. Watch mode and hot reload remain outside LOT-25.


## Developer diagnostics

LOT-26 adds two deliberately distinct read-only workflows:

```bash
pypagekit doctor
pypagekit inspect
```

`doctor` answers whether the current local project environment is usable:

```text
Python / PyPageKit
        ↓
Project root
        ↓
pyproject.toml / site.py
        ↓
dist/ / dist/index.html
        ↓
DiagnosticReport
```

Missing generated output is reported as a warning because a project may simply not have been
built yet. Missing project definition files and malformed project metadata are failures.

`inspect` answers a different question: what can PyPageKit observe about this project without
executing project code? It reports the project root/name, Python and PyPageKit versions, and the
presence of the standard project/output files.

The service boundary remains independent from the CLI:

```text
Typer / Rich
    ↓
doctor / inspect adapters
    ↓
pypagekit.diagnostics
    ↓
immutable result models
```

Neither command modifies files, executes `site.py`, invokes subprocesses, or accesses the
network.


## Renderer extensibility

LOT-27 opens the extensibility line with one concrete extension point rather than automatic plugin
discovery.

```python
from pypagekit.extensions import (
    ExtensionDescriptor,
    RendererExtension,
    RendererRegistry,
)

registry = RendererRegistry(
    (
        RendererExtension(
            ExtensionDescriptor(
                "acme.renderer.custom",
                "Custom Renderer",
                "1.0.0",
            ),
            CustomRenderer,
        ),
    )
)

renderer = registry.create("acme.renderer.custom")
```

The created renderer plugs into the existing build boundary:

```python
from pypagekit.build import BuildPlanner

plan = BuildPlanner(renderer=renderer).plan(site)
```

The built-in HTML renderer is also exposed through an explicit registry:

```python
from pypagekit.extensions import (
    HTML_RENDERER_EXTENSION_ID,
    default_renderer_registry,
)

renderer = default_renderer_registry().create(HTML_RENDERER_EXTENSION_ID)
```

The architecture is deliberately explicit:

```text
ExtensionDescriptor
        ↓
RendererExtension
        ↓
RendererRegistry
        ↓
explicit create(id)
        ↓
Renderer
        ↓
BuildPlanner
```

LOT-27 does not scan installed packages or load Python entry points. Discovery remains LOT-29.


## Build and component extensibility

LOT-28 extends the explicit extension model without introducing arbitrary mutable hooks.

A third-party build planner only needs to satisfy the structural build contract:

```python
from pypagekit import Assets, Site
from pypagekit.build import BuildPlan


class CustomPlanner:
    def plan(
        self,
        site: Site,
        assets: Assets | None = None,
    ) -> BuildPlan: ...
```

It can be registered and injected without subclassing the built-in planner:

```python
from pypagekit.extensions import (
    BuildPlannerExtension,
    BuildPlannerRegistry,
    ExtensionDescriptor,
)

registry = BuildPlannerRegistry(
    (
        BuildPlannerExtension(
            ExtensionDescriptor(
                "acme.build.custom",
                "Custom Planner",
                "1.0.0",
            ),
            CustomPlanner,
        ),
    )
)

planner = registry.create("acme.build.custom")
```

Component extensions contribute ordinary component factories and materialize the existing
`ComponentRegistry`:

```python
from pypagekit.extensions import (
    ComponentExtension,
    ComponentExtensionRegistry,
    ExtensionDescriptor,
)

extensions = ComponentExtensionRegistry(
    (
        ComponentExtension(
            ExtensionDescriptor(
                "acme.components.ui",
                "ACME UI Components",
                "1.0.0",
            ),
            {
                "notice": Notice,
                "hero": Hero,
            },
        ),
    )
)

component_registry = extensions.component_registry()
```

The important boundaries remain:

```text
BuildPlannerExtension
        ↓
BuildPlannerRegistry
        ↓
BuildPlannerProtocol
        ↓
StaticSiteGenerator

ComponentExtension
        ↓
ComponentExtensionRegistry
        ↓
ComponentRegistry
        ↓
ComponentRuntime
        ↓
Renderer
```

LOT-28 still performs no installed-package scanning, no entry-point loading, and no import-time
discovery. Those concerns remain reserved for LOT-29.


## Installed plugin discovery

LOT-29 adds an explicit bridge from standard Python package metadata to the registries introduced in
LOT-27 and LOT-28.

PyPageKit recognizes exactly three entry-point groups:

```text
pypagekit.renderers
pypagekit.build_planners
pypagekit.components
```

A plugin package declares providers in `pyproject.toml`:

```toml
[project.entry-points."pypagekit.renderers"]
"acme.renderer.custom" = "acme_pypagekit:provide_renderer"

[project.entry-points."pypagekit.build_planners"]
"acme.build.custom" = "acme_pypagekit:provide_build_planner"

[project.entry-points."pypagekit.components"]
"acme.components.ui" = "acme_pypagekit:provide_components"
```

Each target is a zero-argument callable. It must return the extension type corresponding to the
group:

```python
def provide_renderer() -> RendererExtension: ...


def provide_build_planner() -> BuildPlannerExtension: ...


def provide_components() -> ComponentExtension: ...
```

The entry-point name is the public extension identity and must exactly match
`extension.descriptor.extension_id`.

Discovery is always explicit:

```python
from pypagekit.extensions import EntryPointDiscovery

plugins = EntryPointDiscovery().discover()

renderer = plugins.renderers.create("acme.renderer.custom")
planner = plugins.build_planners.create("acme.build.custom")
component_registry = plugins.components.component_registry()
```

The execution path is therefore:

```text
installed distribution metadata
        ↓
importlib.metadata.entry_points(...)
        ↓
explicit EntryPointDiscovery.discover()
        ↓
provider callable
        ↓
RendererExtension / BuildPlannerExtension / ComponentExtension
        ↓
existing immutable registry
        ↓
existing runtime/build boundary
```

Creating `EntryPointDiscovery` performs no metadata enumeration and imports no plugin module.
Plugin modules are loaded only during an explicit `discover()` call. Discovery performs no network
access and does not mutate process-global extension state.

LOT-29 intentionally does not add plugin activation/deactivation state, dependency ordering,
compatibility negotiation, or lifecycle callbacks. Those concerns belong to LOT-30.


## Plugin lifecycle and conformance

LOT-30 separates **discovery** from **usability**.

A discovered plugin contribution is not automatically active:

```text
DISCOVERED
    ↓ qualify()
┌───────────────┐
│               │
QUALIFIED    REJECTED
    ↓ activate()
  ACTIVE
    ↓ deactivate()
QUALIFIED
```

The transitions are immutable. Every lifecycle operation returns a new `PluginLifecycle`; the
previous value is unchanged.

### Extension API compatibility

Plugin extensions may declare the PyPageKit extension API they target:

```python
from pypagekit.extensions import (
    PYPAGEKIT_EXTENSION_API_VERSION,
    ExtensionDescriptor,
    RendererExtension,
)


def provide_renderer() -> RendererExtension:
    return RendererExtension(
        ExtensionDescriptor(
            "acme.renderer.custom",
            "ACME Renderer",
            "1.0.0",
            api_version=PYPAGEKIT_EXTENSION_API_VERSION,
        ),
        CustomRenderer,
    )
```

For the `0.7.x` extensibility line, the public extension API identifier is:

```text
0.7
```

This identifier is intentionally separate from the package version `0.8.0a1`. Plugin
compatibility therefore targets a stable extension-contract line instead of a specific package
build.

A missing compatibility declaration or a different API line causes qualification to mark that
contribution as `REJECTED`.

### Qualification

Discovery remains explicit and unchanged:

```python
from pypagekit.extensions import EntryPointDiscovery, PluginLifecycle

discovered = EntryPointDiscovery().discover()
lifecycle = PluginLifecycle.from_discovery(discovered)
qualified = lifecycle.qualify()
```

Qualification validates:

```text
stable extension identity
        ↓
global ID uniqueness across plugin kinds
        ↓
declared PyPageKit extension API
        ↓
API compatibility
        ↓
renderer/build-planner factory conformance
        ↓
component contribution structural conformance
        ↓
QUALIFIED or REJECTED
```

Renderer and build-planner factories are instantiated during explicit qualification so their
existing runtime contracts can be verified. Component factories are not invoked because component
construction may legitimately require author-supplied properties; their registry structure remains
the conformance boundary.

Qualification is fault-isolating: one invalid contribution becomes `REJECTED` rather than
silently becoming usable.

### Activation

Only qualified plugins may become active:

```python
active = qualified.activate()

renderer = active.active_plugins.renderers.create("acme.renderer.custom")
```

Activation can also be selective:

```python
active = qualified.activate(
    (
        "acme.renderer.custom",
        "acme.components.ui",
    )
)
```

Only `active.active_plugins` should be treated as the usable plugin surface. The original discovery
result remains available for inspection, and `qualified.qualified_plugins` exposes every
contribution that passed conformance.

Deactivation is equally explicit:

```python
next_state = active.deactivate(("acme.renderer.custom",))
```

No plugin-defined activation or deactivation callback is executed. Activation is a PyPageKit
registry-selection operation, not an arbitrary side-effect lifecycle.

### Lifecycle invariants

```text
import pypagekit
        → no discovery
        → no plugin import
        → no qualification
        → no activation

EntryPointDiscovery()
        → no discovery

.discover()
        → imports providers explicitly
        → DISCOVERED

PluginLifecycle.from_discovery(...)
        → no factory conformance execution
        → DISCOVERED

.qualify()
        → explicit conformance
        → QUALIFIED / REJECTED

.activate()
        → explicit registry selection
        → ACTIVE
```

There is still no process-global mutable plugin registry, no hidden activation, no network lookup,
and no dependency-resolution engine. The `0.7.x` line now provides the complete explicit
extensibility chain from contract definition through controlled discovery and activation.


## Security hardening

LOT-31 hardens existing trust boundaries without introducing a new authoring model.

### Filesystem output

Build output now rejects symlinks anywhere in the declared output-root path, including ancestors that
exist before the output root itself:

```text
/tmp/projects -> /outside
/tmp/projects/site/dist
     ↑
     rejected before creation
```

Overwrite mode also rejects existing files with more than one hard link. This prevents a path
inside `dist/` from being used as an alias for an inode outside the output tree.

Asset preflight additionally compares existing sources and destinations by filesystem identity,
not only by resolved pathname. A hard-linked asset source/output alias therefore fails before any
file is opened for writing.

The same hard-link protection applies to `pypagekit new --force`: generated project files never
overwrite a multiply-linked inode.

### URL references

Renderer URL validation now rejects:

- malformed percent escapes;
- percent-encoded ASCII control characters;
- percent-encoded unsafe schemes such as `javascript%3A...`;
- encoded scheme obfuscation that would become unsafe after ASCII percent decoding.

The validator still returns the original semantic value after approval; it does not rewrite URLs.

### Development server

The local static server now rejects malformed percent escapes and the DEL control character in
request paths. It also emits defensive response headers:

```text
Cache-Control: no-store
Content-Security-Policy: default-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'
Referrer-Policy: no-referrer
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
```

Directory listings and symlink traversal remain disabled.

### Plugin discovery

Duplicate entry-point names in one PyPageKit plugin group are detected before any target is loaded.
This avoids executing multiple third-party providers before discovering that the registry identity
is ambiguous.

The security model remains explicit:

```text
metadata enumeration
        ↓
duplicate-name validation
        ↓
entry-point identity validation
        ↓
load provider
        ↓
provider execution
        ↓
extension registry
        ↓
qualification
        ↓
activation
```

LOT-31 does not claim sandboxing of third-party Python code. Calling explicit plugin discovery or
qualification may execute trusted installed plugin code by design; the hardening goal is to reduce
avoidable execution and preserve clear trust boundaries.


## Reliability and failure hardening

LOT-32 strengthens failure semantics after LOT-31 hardened trust boundaries.

### Filesystem rollback

`FilesystemWriter` now treats one materialization call as a local rollback transaction.

Before each managed file is mutated, the writer records whether the destination already exists. When
overwrite is enabled, the existing file is snapshotted before modification.

If an exception occurs while writing a later page or copying an asset:

```text
preflight
   ↓
page A written
   ↓
page B overwritten
   ↓
asset copy fails
   ↓
rollback
   ├── remove page A
   ├── restore previous page B
   ├── remove partial asset
   └── remove directories created only by this operation
```

Unplanned existing files are never part of the transaction and remain untouched.

A normal materialization failure is reported as `FilesystemWriteError` with the original exception
available through exception chaining.

If restoring state itself fails, PyPageKit raises the more specific
`FilesystemRollbackError`. This explicitly signals that callers must treat the output tree as
potentially inconsistent.

The same rollback primitive is used by project scaffolding. A failed
`ProjectScaffolder.write()` removes newly generated files and restores managed files that had been
overwritten with `force=True`. A rollback failure is surfaced as
`ProjectScaffoldRollbackError`.

These guarantees apply to exceptions observed by the running Python process. They do not claim
crash consistency across abrupt process termination, operating-system failure, or power loss.

### Renderer failure semantics

Build planning now distinguishes framework errors from unexpected renderer failures.

Known PyPageKit exceptions retain their original public type:

```text
UnsafeUrlError
ValidationError
RenderingError
...
        ↓
propagated unchanged
```

Unexpected third-party renderer exceptions are wrapped as `BuildRenderError` with the affected
route path and the original exception preserved as `__cause__`.

This keeps security/validation errors actionable while adding route context to unknown failures.

### Third-party planner results

`StaticSiteGenerator` now validates the result returned by a structural third-party planner before
calling the filesystem writer.

```text
planner.plan(...)
      ↓
BuildPlan? ── no ──> InvalidBuildPlanError
      │
     yes
      ↓
FilesystemWriter
```

A faulty planner therefore cannot pass an arbitrary object deeper into materialization.

### Extension factory failures

Explicit renderer and build-planner registries now wrap exceptions raised by their zero-argument
factories as `ExtensionFactoryError`.

```text
registry.create(extension_id)
        ↓
extension.factory()
        ↓
unexpected exception
        ↓
ExtensionFactoryError
        ↓
original exception retained as cause
```

Plugin lifecycle qualification continues to isolate such a contribution as `REJECTED`, now with a
stable framework-level failure class rather than an arbitrary third-party exception type.

LOT-32 intentionally does not add retries, background recovery, process supervision, filesystem
journaling, or crash-safe multi-file atomic commits. Those would require stronger operational
semantics than the local library contract currently needs.


## Performance and scalability hardening

LOT-33 reduces avoidable algorithmic and I/O amplification without changing PyPageKit's public
authoring model or weakening the security and rollback guarantees introduced in LOT-31 and LOT-32.

### Build target collision validation

Build target collision detection no longer compares every target with every later target.

Previous conceptual cost:

```text
target 1  × every later target
target 2  × every later target
...
        → O(n²)
```

LOT-33 tracks previously declared files and directory prefixes while visiting targets once:

```text
target
  ↓
exact-file index
  ↓
ancestor-file prefixes
  ↓
required-directory index
  ↓
register target + prefixes
```

The work is now proportional to the total number of path segments across targets rather than the
square of the number of targets. Collision error ordering remains deterministic.

### Immutable lookup indexes

Public declaration order remains unchanged, while hot lookups use private immutable sorted indexes:

```text
Site.route()/has_route()             O(log n)
Assets.asset()/has_target()          O(log n)
ComponentRegistry factory/contains   O(log n)
Extension registry lookup/contains   O(log n)
```

The public tuples (`routes`, `items`, `entries`) remain the canonical immutable surfaces and
retain their existing deterministic order. Private lookup indexes are excluded from equality and
repr semantics.

Repeated `ids`, component-name, and component-registry-name projections are also retained as
immutable cached tuples instead of being rebuilt for each lookup.

### Filesystem preflight

Asset source/output hard-link detection no longer performs an assets × destinations scan.

Existing destination filesystem identities are indexed once by `(st_dev, st_ino)`, then each
asset source performs one identity lookup. Security behavior remains fail-closed and the existing
hard-link conflict errors are unchanged.

### Overwrite rollback snapshots

LOT-32 originally preserved overwritten files by copying their full contents into temporary backup
files. LOT-33 replaces that data copy with a same-directory `os.replace()` move:

```text
old destination
      ↓ os.replace
temporary rollback name
      ↓
write new destination
```

Successful commit removes the rollback name. On failure, rollback moves the original inode back into
place.

This removes an extra full-file read/write cycle for every overwritten output while preserving the
same Python-exception rollback semantics. Existing hard-link protections remain in preflight.

### Component runtime allocation

When a container/fragment/layout region contains no resolvable component changes, the runtime no
longer constructs a speculative replacement tuple merely to discard it. A replacement child list
is allocated only after the first child actually resolves to a different object.

### Plugin discovery

Duplicate entry-point detection now uses one pass over the sorted metadata instead of counting each
name against the complete collection. Provider loading behavior and fail-before-load semantics are
unchanged.

### Scalability qualification

LOT-33 uses deterministic scale-smoke coverage rather than wall-clock assertions. CI exercises:

```text
8,000 safe build targets
2,048 Site routes
2,048 Assets
2,048 component registrations
2,048 renderer extensions
```

The tests assert ordinary semantic behavior at scale and avoid machine-dependent timing thresholds.
Performance regressions therefore remain testable without turning CI scheduling noise into false
failures.

LOT-33 does not introduce parallel rendering, asynchronous filesystem writes, worker pools,
incremental build caching, content hashing, or cross-process build caches. Those are separate
product capabilities rather than hardening requirements.


## Public API stability

LOT-34 establishes the explicit pre-1.0 API inventory.

Human-readable policy:

```text
PUBLIC_API.md
```

Machine-readable source of truth:

```text
PUBLIC_API.toml
```

The core rule is:

```text
public facade import     → compatibility candidate
deep implementation import → internal unless explicitly promoted
```

For example:

```python
from pypagekit.build import BuildPlan  # public stability candidate
from pypagekit.build.model import BuildPlan  # internal import path
```

CI now verifies that every explicit facade `__all__` matches the inventory exactly. CLI command
names, exit semantics, extension entry-point groups, built-in extension IDs, extension API version,
`py.typed`, and the minimum Python version are inventoried as operational contracts.

See [PUBLIC_API.md](PUBLIC_API.md) for the classification policy.


## Compatibility and migration

LOT-35 defines how the public contract may evolve.

Canonical policy:

```text
COMPATIBILITY.md
COMPATIBILITY.toml
```

Active public deprecation registry:

```text
DEPRECATIONS.toml
```

Migration guide:

```text
MIGRATION_0_9_TO_1_0.md
```

The stable-major rule is deliberately strong:

```text
deprecate during 1.x
        ↓
keep compatibility alias through 1.x
        ↓
eligible for removal in 2.0
```

PyPageKit uses the standard `DeprecationWarning` category. At `0.9.0rc1`, the active public
deprecation registry is empty: no supported facade-based application code needs a rename migration.

For the final pre-1.0 migration, applications should eliminate deep implementation imports, enable
deprecation warnings in CI, and validate plugins against the exported extension API compatibility
constant before testing against `0.9.0rc1`.


## 1.0 contract freeze

LOT-36 freezes the release-candidate contract used to qualify PyPageKit 1.0.

Human-readable contract:

```text
API_CONTRACT_1_0.md
```

Machine-readable exact baseline:

```text
API_CONTRACT_1_0.json
```

CI regenerates the runtime contract and compares it exactly with that baseline.

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

The shell CLI is frozen as an operational contract. The Python/Typer adapter under
`pypagekit.cli` remains explicitly provisional.

The plugin compatibility line remains `0.7`; package `1.0.0` does not force an artificial
plugin API renumbering.

The baseline is identical under Python 3.11, 3.12, 3.13, and 3.14.
