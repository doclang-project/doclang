# DocLang

Specification and reference validator for the [DocLang](https://www.doclang.ai/) document format.

This repository contains:

- **[spec.md](./spec.md)** — normative specification
- **`doclang/`** — reference validator (XSD + Schematron, `doclang` CLI on PyPI)
- **`reference/`** — source data for Appendix A (Excel, examples)
- **`exports/`** — generated Word exports from `spec.md`

## Validation

The `doclang` package provides XSD schema and Schematron validation tools via CLI.

Quick usage example:

```bash
uv run doclang validate path/to/file.dclg.xml
```

For details, check out [doclang/README.md](./doclang/README.md).

## Version syncing

The DocLang validator version is derived from git tags (via [setuptools-scm](https://github.com/pypa/setuptools-scm)).
Tag releases as `vMAJOR.MINOR.PATCH` (e.g. `git tag v0.2.0`). On the tag itself the version is `0.2.0`;
the next commit becomes `0.2.0+g<short_sha>` (a `.dYYYYMMDD` suffix is added when the working tree is dirty).

`doclang --version` resolves from **`git describe`** when run inside a git checkout (same
`only-version` rules as setuptools-scm). Otherwise it falls back to installed package metadata
(e.g. wheels without `.git`).

To propagate a version across the spec artifacts, run:

```bash
uv run python utils/sync_version.py 0.4.0   # target release (typical before tagging)
uv run python utils/sync_version.py         # same version as doclang --version (release triple)
```

## Reference generation

To generate the reference from the input Excel file, example DocLang files, and images, and update Appendix A in `spec.md`, run:

```bash
uv run python utils/generate_reference.py reference/input
```

## Word export

To export [spec.md](./spec.md) to Word:

```bash
uv run python utils/export_docx.py
```

Outputs are written under [exports/](./exports/) (`doclang.docx`, and `doclang-styled.docx` when `exports/templates/word.dotx` is present).

## Release workflow

1. **Test** — `uv run pytest`
2. **Prepare release** — `uv run python utils/prepare_release.py TARGET_VERSION`
   (syncs version across artifacts, regenerates Appendix A, writes DOCX exports, and prepends a section to `CHANGELOG.md`; optional `--reference-input reference/input`)
3. **Commit & tag** — once committed to `main`, create and push the tag.
