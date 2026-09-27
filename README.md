# PyPageKit

PyPageKit is a Python-first framework for describing pages as structured Python objects, composing reusable components, rendering safe HTML, and progressively building static sites.

## Status

Current implementation milestone: **LOT-03 — Text Content** (`0.1.0a3`).

Implemented so far:

- typed `src/` package and CI foundations;
- `Node` and `Content` domain foundations;
- immutable `Page` root document object;
- immutable `Text`, `Heading`, and `Paragraph` content primitives;
- explicit domain validation and exceptions.

HTML rendering is intentionally not implemented yet. Domain text stays raw and will be escaped only at the serialization boundary in later LOTs.

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
from pypagekit import Heading, Page, Paragraph, Text


page = Page(
    title="Home",
    content=[
        Heading("Welcome", level=1),
        Paragraph("PyPageKit models pages with Python objects."),
        Text("Literal text content"),
    ],
    lang="en",
    description="Example page",
)
```

`Page` normalizes its content into an immutable tuple. Text content primitives preserve exactly the semantic strings supplied by the author; HTML escaping is not a domain responsibility.

## Source layout

```text
src/
└── pypagekit/
    ├── __init__.py
    ├── py.typed
    ├── domain/
    │   ├── __init__.py
    │   ├── base.py
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

The immediate next milestone is **LOT-04 — Composition Tree**.
