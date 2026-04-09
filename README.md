# DocLang ISO standard

This repo keeps all the documentation for the ISO standardization of DocLang.

## ISO standard

The official ISO standard is described in the Markdown file [iso-standard.md](./iso-standard.md).

To create the Word document, simply run `uv run ./docling_iso/write_iso_draft.py`.

## Validation

The `doclang` package provides XSD schema and Schematron validation tools via CLI.

Quick usage example:

```bash
uv run doclang validate path/to/file.dclg.xml
```

For details, check out [doclang/README.md](./doclang/README.md).
