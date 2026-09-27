# PyPageKit

PyPageKit is a Python-first framework for describing pages as structured Python objects, composing reusable components, rendering safe HTML, and progressively building static sites.

## Status

Current implementation milestone: **LOT-05 — Actions & Media** (`0.1.0b1`).

The first `0.1.x` domain line is now feature-complete.

Implemented so far:

- typed `src/` package and CI foundations;
- `Node` and `Content` domain foundations;
- immutable `Page` root document object;
- immutable `Text`, `Heading`, and `Paragraph` primitives;
- immutable `Container` for ordered recursive composition;
- semantic `Action` / `Media` base types;
- immutable `Link` and `Image` primitives;
- explicit domain validation and exceptions.

HTML rendering is intentionally not implemented yet. The domain describes page structure and references without embedding HTML behavior.

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

## Current domain API

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

`Page` and `Container` normalize composition collections into immutable tuples. Domain strings remain semantic values; HTML escaping and URL safety belong to later rendering/security layers.

## Domain hierarchy

```text
Node
├── Page
└── Content
    ├── Text
    ├── Heading
    ├── Paragraph
    ├── Container
    ├── Action
    │   └── Link
    └── Media
        └── Image
```

## Source layout

```text
src/
└── pypagekit/
    ├── __init__.py
    ├── py.typed
    ├── domain/
    │   ├── __init__.py
    │   ├── action.py
    │   ├── base.py
    │   ├── container.py
    │   ├── media.py
    │   ├── page.py
    │   └── text.py
    └── exceptions/
        ├── __init__.py
        └── domain.py
```

## Roadmap

```text
0.1.x  Domain
0.2.x  Rendering
0.3.x  Components
0.4.x  Routing & Site
0.5.x  Static Build
0.6.x  CLI & Developer Workflow
0.7.x  Extensibility
0.8.x  Hardening
0.9.x  API Freeze
1.0.0  Stable
```

The immediate next milestone is **LOT-06 — HTML Serialization**, beginning the `0.2.x` rendering line.
