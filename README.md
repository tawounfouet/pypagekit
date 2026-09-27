# PyPageKit

PyPageKit is a Python-first framework for describing pages as structured Python objects, composing reusable components, rendering safe HTML, and progressively building static sites.

## Status

Current implementation milestone: **LOT-04 — Composition Tree** (`0.1.0a4`).

Implemented so far:

- typed `src/` package and CI foundations;
- `Node` and `Content` domain foundations;
- immutable `Page` root document object;
- immutable `Text`, `Heading`, and `Paragraph` text primitives;
- immutable `Container` for ordered recursive composition;
- explicit domain validation and exceptions.

HTML rendering is intentionally not implemented yet. The domain describes page structure without embedding HTML behavior.

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
from pypagekit import Container, Heading, Page, Paragraph, Text


page = Page(
    title="Home",
    content=[
        Container(
            children=[
                Heading("Welcome", level=1),
                Paragraph("PyPageKit models pages as composition trees."),
                Container(
                    children=[
                        Text("Nested content remains ordinary Content."),
                    ]
                ),
            ]
        )
    ],
    lang="en",
    description="Example page",
)
```

`Page` and `Container` normalize their content collections into immutable tuples. Text values remain raw semantic data; rendering and HTML escaping belong to later layers.

## Composition model

```text
Page
└── Container
    ├── Heading
    ├── Paragraph
    └── Container
        └── Text
```

## Source layout

```text
src/
└── pypagekit/
    ├── __init__.py
    ├── py.typed
    ├── domain/
    │   ├── __init__.py
    │   ├── base.py
    │   ├── container.py
    │   ├── page.py
    │   └── text.py
    └── exceptions/
        ├── __init__.py
        └── domain.py

tests/
├── test_package.py
└── unit/
    └── domain/
        ├── test_base.py
        ├── test_container.py
        ├── test_page.py
        └── test_text.py
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

The immediate next milestone is **LOT-05 — Actions & Media**.
