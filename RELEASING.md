# Releasing PyPageKit

This document defines the post-1.0 publication procedure for PyPageKit.

Release qualification and publication are deliberately separate:

```text
implementation / compatibility work
        ↓
CI qualification on main
        ↓
versioned stable commit
        ↓
vX.Y.Z tag
        ↓
.github/workflows/release.yml
        ↓
qualified distributions
        ├── GitHub Release
        └── PyPI Trusted Publishing
```

## Publication workflow

The canonical workflow is:

```text
.github/workflows/release.yml
```

It runs only for Git tags matching `v*`. The workflow then rejects any tag that is not an exact
stable SemVer form:

```text
vX.Y.Z
```

The tag must equal the runtime package version exactly:

```text
tag                    v1.0.0
pypagekit.__version__  1.0.0
                       ↓
                     valid
```

A tag such as `v1.0`, `1.0.0`, `v1.0.0rc1`, or a tag whose version differs from
`pypagekit.__version__` is rejected before publication.

## Qualification performed for the tag

Before any upload, the workflow:

- builds wheel and sdist from the tagged source;
- installs the wheel;
- checks installed package and metadata versions;
- verifies Python `>=3.11` metadata;
- verifies Production/Stable classification;
- verifies the installed `py.typed` marker;
- runs `pip check`;
- smoke-tests shell and module CLI entry points;
- generates a real project through `pypagekit new`;
- executes generated `site.py`;
- requires `dist/index.html`;
- runs `pypagekit doctor` and `pypagekit inspect`;
- uploads only those qualified distributions to later publication jobs.

The normal `.github/workflows/ci.yml` remains the authoritative multi-Python quality gate before a
release tag is created.

## GitHub Release

After qualification, the release workflow creates:

```text
PyPageKit X.Y.Z
```

for tag:

```text
vX.Y.Z
```

and uploads the qualified wheel and sdist.

The operation is idempotent: if the GitHub Release already exists, the workflow reuses it and
replaces the attached distribution files.

## PyPI Trusted Publishing

PyPI publication uses OIDC Trusted Publishing rather than a long-lived API token.

The trusted publisher must be configured with exactly:

```text
PyPI project       pypagekit
GitHub owner       tawounfouet
Repository         pypagekit
Workflow filename  release.yml
Environment        pypi
```

For a first publication, configure a **pending publisher** for project `pypagekit`. The first
successful trusted publication creates the PyPI project and converts the pending publisher to a
normal publisher.

The GitHub workflow grants `id-token: write` only to the PyPI publication job.

## GitHub environment

Create a GitHub Actions environment named:

```text
pypi
```

Recommended protection:

- require manual approval before deployment;
- restrict deployment to release tags;
- limit approvers to trusted maintainers.

No PyPI API token is required.

## Publishing a stable release

Preconditions:

- `main` contains the intended release commit;
- CI on `main` is fully green;
- `pypagekit.__version__` equals the intended stable version;
- `CHANGELOG.md` contains that version;
- no unreviewed public-contract drift exists;
- PyPI Trusted Publisher configuration matches `release.yml` and environment `pypi`.

Then create and push the tag:

```bash
git switch main
git pull --ff-only

git tag -a v1.0.0 -m "PyPageKit 1.0.0"
git push origin v1.0.0
```

For future releases, replace `1.0.0` with the package version being published.

The pushed tag starts the publication workflow automatically.

## Failure policy

A failed publication must not be worked around by changing the tag target or rebuilding artifacts
locally.

Instead:

1. diagnose the failed GitHub Actions job;
2. correct workflow or publisher configuration through a reviewed commit when necessary;
3. keep the original release commit immutable;
4. rerun the failed workflow when the fix is configuration-only;
5. if package content itself must change, issue a new version rather than replacing an already
   published PyPI release.

PyPI files are immutable for a published version. A release version must therefore be treated as
permanent once uploaded.

## Relationship to the 1.0 contract

The publication workflow does not redefine the compatibility baseline.

For PyPageKit 1.0.0:

```text
API_CONTRACT_1_0.json
```

remains the LOT-36 historical baseline, and LOT-37 remains the qualification evidence for the
package contents.

Publication only distributes the already-qualified version.
