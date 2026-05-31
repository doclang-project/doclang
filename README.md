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

Release preparation derives the target version from git tags (`vMAJOR.MINOR.PATCH`, e.g. `v0.3.0`)
and writes the release triple to `pyproject.toml`, the XSD, and the reference Excel.

`doclang --version` reads from **`pyproject.toml`** in a checkout, or from installed package
metadata on PyPI (where git tags are not available).

To propagate a version across artifacts, run:

```bash
uv run python utils/sync_version.py 0.4.0   # explicit target release (typical before tagging)
uv run python utils/sync_version.py         # release triple from latest git tag
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
