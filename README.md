# PyPageKit

PyPageKit is a Python-first framework for describing pages as structured Python objects, composing reusable components, rendering safe HTML, and progressively building static sites.

## Status

Current implementation milestone: **LOT-13 — Reusable Components** (`0.3.0b1`).

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
- built-in reusable components composed entirely from the existing domain primitives.

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
0.3.x  Components              ← current
0.4.x  Routing & Site
0.5.x  Static Build
0.6.x  CLI & Developer Workflow
0.7.x  Extensibility
0.8.x  Hardening
0.9.x  API Freeze
1.0.0  Stable
```

The current release line is **`0.3.x — Components`**. The next milestone is **LOT-14 — Slots & Composition**.


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

Dynamic slots remain a later concern in LOT-14.


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

Dynamic named slots are intentionally deferred to LOT-14.
