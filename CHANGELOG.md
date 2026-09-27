# Changelog

All notable changes to PyPageKit will be documented in this file.

## [Unreleased]

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
