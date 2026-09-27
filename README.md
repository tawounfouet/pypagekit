# PyPageKit

PyPageKit is a Python-first framework for describing pages as structured Python objects, composing reusable components, rendering safe HTML, and progressively building static sites.

## Status

Current implementation milestone: **LOT-06 — HTML Serialization** (`0.2.0a1`).

The `0.1.x` domain line is feature-complete, and `0.2.x` now begins with a pure HTML serialization boundary.

Implemented so far:

- typed `src/` package and CI foundations;
- structured immutable page/content domain;
- text, composition, action, and media primitives;
- context-specific HTML text/attribute escaping;
- deterministic HTML5 ordinary-element serialization;
- canonical HTML5 void-element serialization;
- structural validation for tags and attributes;
- rendering/serialization error hierarchy.

The serializer still does **not** know how to render a `Page`, `Heading`, `Link`, or any other domain object. That mapping begins in LOT-07.

## Requirements

- Python 3.11+

The minimum Python version is provisional during the pre-1.0 roadmap and can be revisited before the compatibility freeze.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate  # Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

Run the quality gates:

```bash
ruff check .
ruff format --check .
mypy
pytest
python -m build
```

## Domain example

```python
from pypagekit import Container, Heading, Image, Link, Page, Paragraph


page = Page(
    title="Home",
    content=[
        Container(
            children=[
                Heading("Welcome", level=1),
                Paragraph("PyPageKit models pages as structured Python objects."),
                Link(label="About", href="/about"),
                Image(src="/assets/logo.png", alt="Project logo"),
            ]
        )
    ],
)
```

## Serialization boundary

LOT-06 introduces the internal transformation:

```text
semantic string
      ↓
escape_text / escape_attribute
      ↓
HTML serializer
      ↓
HTML fragment string
```

For example, LOT-07 will be able to map:

```text
Heading("A & B")
      ↓
escape_text("A & B")
      ↓
serialize_element("h1", content="A &amp; B")
      ↓
<h1>A &amp; B</h1>
```

The domain continues to store the original value `"A & B"`.

## Architecture

```text
Domain
  ↓
[LOT-07 HtmlRenderer]
  ↓
Escaping
  ↓
HTML Serializer
  ↓
str
```

## Roadmap

```text
0.1.x  Domain                  ✅ feature-complete
0.2.x  Rendering               ← current
0.3.x  Components
0.4.x  Routing & Site
0.5.x  Static Build
0.6.x  CLI & Developer Workflow
0.7.x  Extensibility
0.8.x  Hardening
0.9.x  API Freeze
1.0.0  Stable
```

The immediate next milestone is **LOT-07 — HTML Renderer**, which connects the domain tree to these serializer primitives.
