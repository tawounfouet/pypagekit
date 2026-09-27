# PyPageKit Implementation Status

| LOT | Scope | Status | Target |
|---|---|---|---|
| LOT-01 | Project Foundations | QUALIFIED | `0.1.0a1` |
| LOT-02 | Core Domain Foundations | QUALIFIED | `0.1.0a2` |
| LOT-03 | Text Content | QUALIFIED | `0.1.0a3` |
| LOT-04 | Composition Tree | QUALIFIED | `0.1.0a4` |
| LOT-05 | Actions & Media | QUALIFIED | `0.1.0b1` |
| LOT-06 | HTML Serialization | QUALIFIED | `0.2.0a1` |
| LOT-07 | HTML Renderer | QUALIFIED | `0.2.0a2` |
| LOT-08 | Security & Escaping | QUALIFIED | `0.2.0b1` |
| LOT-09 | Page Metadata | QUALIFIED | `0.2.0b2` |
| LOT-10 | Attributes & Styling Hooks | QUALIFIED | `0.2.0b3` |

## LOT-07 exit criteria

- [x] public `Renderer` protocol exists
- [x] public `HtmlRenderer` implementation exists
- [x] `Text` renders as escaped text
- [x] `Heading` maps levels 1 through 6 to `h1` through `h6`
- [x] `Paragraph` maps to `p`
- [x] `Container` maps to `div` and renders children recursively
- [x] `Link` maps to `a`
- [x] `Image` maps to HTML5 `img`
- [x] `Page` renders a complete compact HTML5 document
- [x] page language and title are serialized safely
- [x] UTF-8 charset is present
- [x] unsupported nodes fail explicitly
- [x] rendering is deterministic
- [x] rendering does not mutate domain objects
- [x] renderer performs no filesystem or network I/O
- [x] `Page.description` remains deferred to LOT-09
- [x] URL scheme policy remains deferred to LOT-08
- [x] integration tests prove `Page → HTML`

Next: **LOT-09 — Page Metadata**.

## LOT-07 qualification evidence

- branch implementation prepared for CI qualification
- first end-to-end in-memory `Page → HTML` flow now exists
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-08 exit criteria

- [x] text content remains escaped by default
- [x] attribute values remain escaped in attribute context
- [x] link destinations use an explicit scheme allowlist
- [x] image sources use an explicit scheme allowlist
- [x] relative, anchor, query, and protocol-relative references remain supported
- [x] active/local-resource URL schemes are rejected
- [x] ASCII control characters in URL references are rejected
- [x] mixed-case unsafe schemes are rejected
- [x] whitespace-obfuscated unsafe schemes are rejected
- [x] nested composition does not bypass escaping
- [x] page title cannot break out into markup
- [x] attribute breakout payloads remain inert
- [x] no raw-HTML or escape-disable bypass exists
- [x] pre-escaped strings are not treated as trusted HTML
- [x] security policy does not mutate domain values
- [x] adversarial security tests cover the complete current rendering pipeline

Next: **LOT-09 — Page Metadata**.

## LOT-08 qualification evidence

- dedicated `tests/security/` corpus added
- URL validation occurs before HTML attribute serialization
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-09 exit criteria

- [x] page title remains rendered in `<title>`
- [x] page language remains rendered on the root `html` element
- [x] UTF-8 charset remains first in the head
- [x] optional page description renders as `<meta name="description">`
- [x] absent description emits no metadata element
- [x] empty description remains explicitly representable
- [x] description values are attribute-escaped safely
- [x] description metadata cannot inject active markup or attributes
- [x] head metadata ordering is deterministic
- [x] rendering does not mutate page metadata
- [x] no new metadata abstraction is introduced prematurely

Next: **LOT-10 — Attributes & Styling Hooks**.

## LOT-09 qualification evidence

- existing `Page` metadata fields are now fully represented in HTML
- deterministic head assembly is covered by integration tests
- security corpus covers description attribute breakout attempts
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate


## LOT-10 exit criteria

- [x] public immutable `Attributes` value object exists
- [x] `id`, class tokens, and `title` are supported
- [x] `data-*` hooks are generated from validated suffixes
- [x] `aria-*` hooks are generated from validated suffixes
- [x] classes preserve declaration order
- [x] data/ARIA mappings normalize deterministically
- [x] `Heading`, `Paragraph`, `Container`, `Link`, and `Image` accept attributes
- [x] `Text` remains attribute-free
- [x] intrinsic `href`, `src`, and `alt` remain controlled by their domain objects
- [x] arbitrary event-handler and style keywords are not supported
- [x] author values are escaped at serialization time
- [x] existing output is unchanged when attributes are omitted
- [x] rendering remains deterministic
- [x] adversarial tests cover attribute breakout attempts

Next: **LOT-11 — Component Model**.

## LOT-10 qualification evidence

- controlled domain attribute surface added without `dict[str, Any]`
- renderer maps domain hooks to serializer attributes through an internal adapter
- security corpus covers id/class/title/data/aria injection attempts
- GitHub CI is the authoritative Ruff, formatting, mypy, pytest, and packaging gate
