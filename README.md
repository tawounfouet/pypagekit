# PyPageKit

PyPageKit is a Python-first framework for describing pages as structured Python objects, composing reusable components, rendering safe HTML, and progressively building static sites.

## Status

Current implementation milestone: **LOT-02 — Core Domain Foundations** (`0.1.0a2`).

Implemented so far:

- typed `src/` package and CI foundations;
- `Node` as the base domain node;
- `Content` as the base type for page content;
- immutable `Page` root document object;
- early domain validation and explicit exceptions.

Rendering and concrete text content start in subsequent LOTs.

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
from pypagekit import Content, Node, Page


class CustomContent(Content):
    pass


page = Page(
    title="Home",
    content=[CustomContent()],
    lang="en",
    description="Example page",
)
```

`Page` normalizes its content into an immutable tuple and rejects objects that do not derive from `Content`.

## Source layout

```text
src/
└── pypagekit/
    ├── __init__.py
    ├── py.typed
    ├── domain/
    │   ├── __init__.py
    │   ├── base.py
    │   └── page.py
    └── exceptions/
        ├── __init__.py
        └── domain.py

tests/
├── test_package.py
└── unit/
    └── domain/
        ├── test_base.py
        └── test_page.py
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

The immediate next milestone is **LOT-03 — Text Content**.
