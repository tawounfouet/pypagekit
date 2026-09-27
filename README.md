# PyPageKit

PyPageKit is a Python-first framework for describing pages as structured Python objects, composing reusable components, rendering safe HTML, and progressively building static sites.

## Status

Current implementation milestone: **LOT-19 — Assets** (`0.5.0a1`).

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
- declarative static assets with validated publish targets and no filesystem I/O.

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
0.5.x  Static Build              ← current
0.6.x  CLI & Developer Workflow
0.7.x  Extensibility
0.8.x  Hardening
0.9.x  API Freeze
1.0.0  Stable
```

The current release line is **`0.5.x — Static Build`**. The next milestone is **LOT-20 — Build Pipeline**.


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
