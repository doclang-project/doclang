# DocLang ISO standard

This repo keeps all the documentation for the ISO standardization of DocLang.

## Version syncing

The DocLang validator version is governed in `pyproject.toml`.
To propagate the version across the standard, run:

```bash
uv run python utils/sync_version.py
```

## Reference generation

To generate the reference from the input Excel file & example DocLang & image files and update Appendix A in `iso-standard.md`, run:

```bash
uv run python utils/generate_reference.py reference/input
```

## Word document generation

The official ISO standard is described in the Markdown file [iso-standard.md](./iso-standard.md).

To create the Word document, simply run:

```bash
uv run python utils/write_iso_draft.py
```

## Validation

The `doclang` package provides XSD schema and Schematron validation tools via CLI.

Quick usage example:

```bash
uv run doclang validate path/to/file.dclg.xml
```

For details, check out [doclang/README.md](./doclang/README.md).
