# PyPageKit 1.0 Release Qualification

LOT-37 is the final qualification gate for **PyPageKit 1.0.0**.

It is intentionally a **release qualification lot, not a feature lot**. The public 1.0 contract was
frozen by LOT-36 at `0.9.0rc1` and is preserved byte-for-byte by LOT-37.

## Release baseline

```text
LOT-36
0.9.0rc1
    ↓
API_CONTRACT_1_0.json
Git blob d417cf778b0a767c3c0016633ec0d7f3c69e191a
    ↓
LOT-37 qualification
    ↓
1.0.0
```

The release gate verifies both:

1. the runtime still generates the exact frozen contract; and
2. the committed `API_CONTRACT_1_0.json` is the exact LOT-36 file.

Changing the generator and baseline together is therefore not sufficient to bypass the freeze.

## Qualification matrix

The supported Python matrix is:

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

## Distribution qualification

The release package job must prove:

- both sdist and wheel build successfully;
- the wheel installs successfully;
- installed package version is exactly `1.0.0`;
- installed metadata declares `Requires-Python >=3.11`;
- installed metadata declares `Development Status :: 5 - Production/Stable`;
- the installed PEP 561 `py.typed` marker exists;
- `pip check` reports no dependency conflicts;
- the source distribution installs in a fresh virtual environment;
- the installed sdist reports version `1.0.0`.

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

The frozen shell contract remains:

```text
commands: doctor, inspect, new, serve
root options: --help, --version
exit codes: 0 success, 1 execution failure, 2 usage failure
```

The Python/Typer object `pypagekit.cli.app` remains provisional and is not promoted by LOT-37.

## Generated-project qualification

A real project is created from the installed wheel:

```bash
pypagekit new <temporary-project>
```

Its generated dependency must be:

```text
pypagekit>=1.0.0,<1.1
```

The generated `site.py` is then executed and must produce:

```text
dist/index.html
```

Finally, `pypagekit doctor` and `pypagekit inspect` are executed inside that generated project.

## Extension compatibility

The package release version and plugin compatibility version remain independent.

PyPageKit 1.0.0 therefore intentionally retains:

```text
PYPAGEKIT_EXTENSION_API_VERSION = "0.7"
```

LOT-37 must not manufacture an extension API 1.0 migration where no contract change exists.

## Deprecation state

The 1.0.0 release starts with:

```text
active public deprecations = 0
```

Future evolution is governed by `COMPATIBILITY.md` and `COMPATIBILITY.toml`.

## Release exit criteria

LOT-37 is complete only when:

- [ ] version is exactly `1.0.0`;
- [ ] LOT-36 contract JSON is byte-for-byte unchanged;
- [ ] frozen runtime contract matches the baseline;
- [ ] Python 3.11 qualification is green;
- [ ] Python 3.12 qualification is green;
- [ ] Python 3.13 qualification is green;
- [ ] Python 3.14 qualification is green;
- [ ] wheel build and installation are green;
- [ ] sdist build and clean-environment installation are green;
- [ ] installed metadata and PEP 561 marker are qualified;
- [ ] installed CLI smoke tests are green;
- [ ] generated-project end-to-end smoke test is green;
- [ ] extension API remains `0.7`;
- [ ] active public deprecation registry is empty;
- [ ] final README, changelog, roadmap, and implementation status are aligned;
- [ ] pull-request CI is fully green;
- [ ] LOT-37 is merged to `main`;
- [ ] final `main` CI is green.

## Post-1.0

No post-1.0 feature work belongs in LOT-37.

After this lot, the historical implementation train from LOT-01 through LOT-37 is closed. New
feature work belongs to a separately versioned post-1.0 roadmap.
