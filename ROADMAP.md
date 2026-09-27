# PyPageKit Roadmap

This file freezes the remaining implementation train from the qualified `0.6.0b2` baseline to
`1.0.0`.

## Release train

| Line | Theme | Lots |
|---|---|---|
| `0.1.x` | Domain | LOT-01..05 |
| `0.2.x` | Rendering | LOT-06..10 |
| `0.3.x` | Components | LOT-11..15 |
| `0.4.x` | Routing & Site | LOT-16..18 |
| `0.5.x` | Static Build | LOT-19..22 |
| `0.6.x` | CLI & Developer Workflow | LOT-23..26 |
| `0.7.x` | Extensibility | LOT-27..30 |
| `0.8.x` | Hardening | LOT-31..33 |
| `0.9.x` | API Freeze | LOT-34..36 |
| `1.0.0` | Stable | LOT-37 |

## Remaining lots

| LOT | Scope | Target |
|---|---|---|
| LOT-27 | Extension Contracts & Renderer Registry | `0.7.0a1` |
| LOT-28 | Build & Component Extension Points | `0.7.0a2` |
| LOT-29 | Plugin Discovery & Entry Points | `0.7.0b1` |
| LOT-30 | Plugin Lifecycle & Conformance | `0.7.0b2` |
| LOT-31 | Security Hardening | `0.8.0a1` |
| LOT-32 | Reliability & Failure Hardening | `0.8.0a2` |
| LOT-33 | Performance & Scalability Hardening | `0.8.0b1` |
| LOT-34 | Public API Inventory & Stability Classification | `0.9.0a1` |
| LOT-35 | Compatibility, Deprecation & Migration | `0.9.0b1` |
| LOT-36 | 1.0 Contract Freeze | `0.9.0rc1` |
| LOT-37 | 1.0 Release Qualification | `1.0.0` |

## Extensibility sequencing

Extensibility is intentionally introduced from explicit contracts outward:

```text
LOT-27
explicit renderer extension registry
        ↓
LOT-28
additional build/component extension points
        ↓
LOT-29
package discovery through Python entry points
        ↓
LOT-30
plugin lifecycle and conformance
```

The core rules are:

- no process-global mutable plugin registry;
- no import-time discovery;
- no dynamic import strings in domain objects;
- discovery must feed explicit registries rather than bypass them;
- third-party output continues through existing security and validation boundaries;
- an extension point must be exercised directly before automatic discovery is added.

## Hardening sequencing

```text
security
   ↓
reliability / failure semantics
   ↓
performance / scalability
```

Hardening must preserve deterministic output and explicit failure behavior.

## 1.0 sequencing

```text
public API inventory
        ↓
stability classification
        ↓
compatibility + deprecation policy
        ↓
contract freeze
        ↓
release qualification
        ↓
1.0.0
```

LOT-37 is a qualification lot, not a feature lot.
