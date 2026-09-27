# Changelog

All notable changes to PyPageKit will be documented in this file.

## [Unreleased]

## [0.3.0a1]

### Added

- Public abstract `Component(Content)` model with `compose() -> Content`.
- Public `ComponentRuntime` for explicit component resolution.
- Recursive resolution of components returned directly or nested inside containers.
- Runtime validation that `compose()` returns `Content`.
- Identity-based component cycle detection.
- Configurable component-resolution depth guard for recursively generated components.
- Transparent `HtmlRenderer` integration through the component runtime.
- LOT-11 tests for composition, nesting, immutability boundaries, cycles, depth protection, escaping, and URL security.

### Design

- Components compose domain structure; they do not render HTML.
- The renderer resolves a component to ordinary content before applying the existing rendering pipeline.
- `Component` remains a `Content`, so it can already appear anywhere `Page` or `Container` accepts content.
- The runtime recreates a container only when one of its descendants actually resolves to different content.
- Layouts, reusable component catalogues, slots, and registries remain outside LOT-11.


## [0.2.0b3]

### Added

- Public immutable `Attributes` model for controlled author-facing HTML hooks.
- Support for `id`, ordered CSS class tokens, `title`, `data-*`, and `aria-*`.
- Attribute support on `Heading`, `Paragraph`, `Container`, `Link`, and `Image`.
- Internal domain-to-HTML attribute mapping that preserves intrinsic attributes such as `href`, `src`, and `alt`.
- Validation for class tokens and data/ARIA attribute suffixes.
- Integration and security coverage for deterministic rendering and attribute injection resistance.

### Security

- No arbitrary attribute dictionary is exposed by the domain model.
- Event-handler attributes and inline `style` are not part of the LOT-10 API.
- Author values remain semantic strings and are escaped at the HTML serialization boundary.
- `data-*` and `aria-*` names are namespaced from validated lowercase suffixes.

### Design

- `Text` remains a text fragment and therefore has no attribute surface.
- Intrinsic link/image attributes remain owned by `Link` and `Image`, not by `Attributes`.
- Class token order is preserved; data/ARIA mappings are normalized deterministically.
- The generic attribute surface remains intentionally narrow until real component use cases justify expansion.


## [0.2.0b2]

### Added

- Rendering of `Page.description` as a deterministic HTML meta description.
- Dedicated head-content assembly preserving the order `charset → title → description`.
- Integration tests for optional, empty, escaped, and deterministic description metadata.
- Security coverage proving description metadata cannot break out of its attribute context.

### Design

- The existing `Page` metadata model remains intentionally small: `title`, `lang`, and optional `description`.
- `description=None` emits no meta description.
- `description=""` remains explicitly representable.
- Metadata values remain semantic domain strings and are escaped only at the HTML serialization boundary.
- Canonical URLs, stylesheets, additional head entries, and richer metadata remain outside LOT-09.


## [0.2.0b1]

### Added

- Render-time URL safety validation for links and images.
- Explicit allowlists for link schemes (`http`, `https`, `mailto`) and image schemes (`http`, `https`).
- `SecurityError` and `UnsafeUrlError` rendering exceptions.
- Adversarial XSS tests covering active markup, attribute breakout attempts, nested composition, unsafe URL schemes, control characters, and pre-escaped input.

### Security

- Relative references, anchors, query references, and protocol-relative references remain supported.
- Active or local-resource schemes such as `javascript:`, `data:`, `vbscript:`, `file:`, and unsupported schemes are rejected at render time.
- URL values remain semantic domain strings and are validated before attribute-context escaping.
- ASCII control characters are rejected in URL references.
- Text and attribute escaping continue to happen exactly at the HTML boundary.
- No `RawHtml`, `SafeHtml`, `escape=False`, or equivalent bypass is introduced.

### Design

- URL safety belongs to the rendering/security boundary rather than mutating the domain model.
- Validation returns the original URL value after approval; output normalization is not performed.
- The serializer remains syntax-focused and does not own URL policy.


## [0.2.0a2]

### Added

- Public `Renderer` protocol.
- Public `HtmlRenderer` implementation.
- Explicit domain-to-HTML dispatch for `Text`, `Heading`, `Paragraph`, `Container`, `Link`, `Image`, and `Page`.
- Recursive ordered rendering for composition trees.
- Complete compact HTML5 document rendering for `Page`.
- `UnsupportedNodeError` for domain nodes not supported by the renderer.
- LOT-07 unit and integration coverage for fragments, nested trees, complete documents, determinism, escaping, and unsupported nodes.

### Design

- `HtmlRenderer.render(node) -> str` is the first public representation contract.
- Domain objects remain renderer-agnostic and never render themselves.
- `Container` maps to `div` in the initial HTML renderer.
- `Page` emits doctype, `html lang`, UTF-8 charset, `title`, and `body`.
- Richer page metadata such as `description` remains deferred to LOT-09.
- URL scheme safety remains deferred to LOT-08; LOT-07 still benefits from attribute-context escaping supplied by LOT-06.
- Rendering performs no filesystem or network I/O.

## [0.2.0a1]

### Added

- Pure HTML5 text and attribute escaping primitives.
- Deterministic serialization for ordinary HTML elements.
- Canonical serialization for HTML5 void elements.
- HTML5 doctype serialization.
- Structural validation for tag and attribute names.
- Scalar and boolean HTML attribute serialization.
- Rendering/serialization exception hierarchy.
- LOT-06 tests for escaping, determinism, Unicode, void elements, boolean attributes, and invalid structural names.

### Design

- Serialization is domain-agnostic and performs no filesystem or network I/O.
- Element content is treated as a trusted serialized fragment; semantic user text must cross the explicit text-escaping boundary first.
- Attribute order is canonicalized lexicographically for deterministic output.
- `None` and `False` omit attributes, `True` emits a name-only boolean attribute, and empty strings are preserved.
- `script` and `style` are rejected by the generic element serializer because they require dedicated raw-text contexts.
- The serializer is implementation infrastructure and is not exported from the package root.
- Domain-to-HTML mapping remains deferred to LOT-07.

## [0.1.0b1]

### Added

- `Action` and `Media` semantic base types in the domain namespace.
- Immutable `Link` action content primitive.
- Immutable `Image` media content primitive.
- Structural validation for empty link destinations and image sources.
- `InvalidLinkHrefError` and `InvalidImageSourceError`.
- LOT-05 tests covering composition, immutability, Unicode, destination/source forms, and decorative images.

### Design

- `Link.label`, `Link.href`, `Image.src`, and `Image.alt` preserve authored strings exactly.
- Empty link labels remain representable.
- Empty image `alt` values are explicitly valid for decorative images.
- URL scheme safety is intentionally deferred to the rendering/security boundary in LOT-08 rather than embedded in the domain model.

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
