# PyPageKit 1.1 Release Qualification

LOT-44 is the final qualification gate for **PyPageKit 1.1.0**.

It is intentionally a **release qualification lot, not a feature lot**. The public 1.1 contract was
frozen by LOT-43 at `1.1.0rc1` and must remain byte-for-byte unchanged during LOT-44.

## Release baseline

```text
LOT-43
1.1.0rc1
    ↓
API_CONTRACT_1_1.json
Git blob b9c752264ab623e570e70ea19433a60806e2df78
    ↓
LOT-44 qualification
    ↓
1.1.0
```

The historical 1.0 compatibility floor also remains unchanged:

```text
API_CONTRACT_1_0.json
Git blob d417cf778b0a767c3c0016633ec0d7f3c69e191a
```

The stable release gate therefore proves three independent properties:

1. the runtime still exactly matches the frozen 1.1 snapshot;
2. the committed 1.1 snapshot is exactly the file accepted by LOT-43;
3. the accepted 1.1 contract still remains compatible with the immutable 1.0 floor.

Changing a generator and a baseline together is not sufficient to bypass these release checks.

## Qualification matrix

The supported Python matrix remains:

```text
Python 3.11
Python 3.12
Python 3.13
Python 3.14
```

Every Python line must pass:

```text
ruff check .
ruff format --check .
mypy
pytest
```

The test suite includes both:

```text
1.0 compatible-superset gate
1.1 exact contract gate
```

## Distribution qualification

The release package job must prove:

- both sdist and wheel build successfully;
- the installed wheel reports package version exactly `1.1.0`;
- installed distribution metadata reports version exactly `1.1.0`;
- installed metadata declares `Requires-Python >=3.11`;
- installed metadata declares `Development Status :: 5 - Production/Stable`;
- the installed PEP 561 `py.typed` marker exists;
- `pip check` reports no dependency conflicts;
- the source distribution installs in a fresh virtual environment;
- the installed source distribution reports version exactly `1.1.0`.

## CLI qualification

The installed wheel must successfully expose:

```text
pypagekit --version
pypagekit --help
pypagekit new --help
pypagekit serve --help
pypagekit doctor --help
pypagekit inspect --help
python -m pypagekit --version
python -m pypagekit --help
```

The shell CLI contract frozen by LOT-43 includes:

```text
commands:
  doctor
  inspect
  new
  serve

serve options:
  --host
  --port
  -p
  --watch
  --entry
  --poll-interval
  --debounce-interval

exit codes:
  0 success
  1 execution failure
  2 usage failure
```

The Python/Typer `pypagekit.cli` facade remains provisional and is not promoted by LOT-44.

## Generated-project qualification

A real project must be created from the installed wheel:

```bash
pypagekit new <temporary-project>
```

Its generated dependency must be exactly:

```text
pypagekit>=1.1.0,<1.2
```

The generated project must continue to document:

```bash
pypagekit serve --watch
```

Its `site.py` must execute successfully and produce:

```text
dist/index.html
```

Finally, `pypagekit doctor` and `pypagekit inspect` are executed inside that generated project.

## Contract preservation

LOT-44 must not alter either frozen contract file.

Expected Git blob identities:

```text
API_CONTRACT_1_0.json
d417cf778b0a767c3c0016633ec0d7f3c69e191a

API_CONTRACT_1_1.json
b9c752264ab623e570e70ea19433a60806e2df78
```

The runtime contract remains version-independent through the dedicated version symbol descriptor, so
promoting `1.1.0rc1` to `1.1.0` must not require a contract refresh.

## Extension compatibility

The package version and extension API remain independent compatibility dimensions.

PyPageKit 1.1.0 intentionally retains:

```text
PYPAGEKIT_EXTENSION_API_VERSION = "0.7"
```

LOT-44 introduces no plugin migration.

## Deprecation state

The stable 1.1.0 release starts with:

```text
active public deprecations = 0
```

Future evolution remains governed by `COMPATIBILITY.md` and `COMPATIBILITY.toml`.

## Release exit criteria

LOT-44 is complete only when:

- [x] package version is exactly `1.1.0`;
- [x] public API metadata tracks `1.1.0`;
- [x] compatibility metadata tracks `1.1.0`;
- [x] deprecation metadata tracks `1.1.0`;
- [x] `API_CONTRACT_1_0.json` is byte-for-byte unchanged;
- [x] `API_CONTRACT_1_1.json` is byte-for-byte unchanged;
- [x] runtime exactly matches the frozen 1.1 contract;
- [x] the 1.1 contract remains compatible with the frozen 1.0 floor;
- [x] generated projects depend on `pypagekit>=1.1.0,<1.2`;
- [x] extension API remains `0.7`;
- [x] active public deprecations remain zero;
- [ ] Python 3.11 qualification is green;
- [ ] Python 3.12 qualification is green;
- [ ] Python 3.13 qualification is green;
- [ ] Python 3.14 qualification is green;
- [ ] wheel qualification is green;
- [ ] sdist qualification is green;
- [ ] installed CLI smoke tests are green;
- [ ] generated-project smoke test is green;
- [ ] pull-request CI is fully green;
- [ ] post-merge main CI is fully green.

## After 1.1.0

No feature work belongs in LOT-44.

Once the stable release is qualified, the complete `1.1.x — Incremental Developer Experience`
implementation train is closed. Any later capability belongs to a separately planned compatible
minor line or patch release.
