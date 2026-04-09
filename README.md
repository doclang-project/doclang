# DocLang ISO standard

This repo keeps all the documentation for the ISO standardization of DocLang.

## ISO standard

The official ISO standard is described in the Markdown file [iso-standard.md](./iso-standard.md).

To create the Word document, simply run `uv run ./docling_iso/write_iso_draft.py`.

## Validation

The `doclang` package provides XSD schema and Schematron validation tools via CLI.

### Quick Start

> [!TIP]
> If running from local repo clone, prepend command below with `uv run `.

Validate a document:

```bash
doclang validate path/to/document.xml
```

### Development

Run tests:

```bash
uv run pytest
```

See [doclang/README.md](./doclang/README.md) for complete documentation on:
- XSD schema structure and validation
- Schematron business rules
- CLI usage and options
- Namespace injection for documents without xmlns
- Running tests with pytest
