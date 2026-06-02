# Contributing

Thanks for helping improve the DocLang standard and reference validator.

## Prerequisites

- [Python](https://www.python.org/) 3.10 or newer
- [uv](https://docs.astral.sh/uv/) for dependency management and running scripts

## Getting started

Clone the repository and install dependencies (including the `dev` group used for reference generation and DOCX export):

```bash
uv sync
```

CI installs only the `ci` group (`uv sync --frozen --no-default-groups --group ci`). For full local development, use `uv sync` without those flags so `dev` dependencies are available.

## Repository layout

- **`spec.md`** — normative specification
- **`doclang/`** — reference validator (XSD, Schematron, CLI); see [doclang/README.md](./doclang/README.md) for package usage
- **`reference/`** — source data for Appendix A (Excel, examples)
- **`exports/`** — generated Word exports from `spec.md`
- **`utils/`** — maintenance scripts (version sync, reference generation, DOCX export, release preparation)
- **`tests/`** — pytest suite and fixture DocLang XML under `tests/data/`

## Checks and tests

Run the full test suite:

```bash
uv run pytest
```

Run the same checks as CI (Ruff, MyPy, pytest, lockfile consistency):

```bash
uv sync --frozen --no-default-groups --group ci
pre-commit run --all-files
```

Install pre-commit hooks locally (optional):

```bash
uv run pre-commit install
```

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

For maintainers preparing a release:

1. **Test** — `uv run pytest`
2. **Prepare release** — `uv run python utils/prepare_release.py TARGET_VERSION`
   (syncs version across artifacts, regenerates Appendix A, writes DOCX exports, and prepends a section to `CHANGELOG.md`; optional `--reference-input reference/input`)
   - Make any manual changes needed (e.g. ToC regeneration on DOCX file, export to PDF etc.)
3. **Commit & tag** — once committed to `main`, create and push the tag.
