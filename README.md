# DocLang ISO standard

This repo keeps all the documentation for the ISO standardization of DocLang.

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

To propagate a version across the standard artifacts, run:

```bash
uv run python utils/sync_version.py 0.4.0   # target release (typical before tagging)
uv run python utils/sync_version.py         # same version as doclang --version (release triple)
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

## Release workflow

1. **Test** — `uv run pytest`
2. **Prepare release** — `uv run python utils/prepare_release.py TARGET_VERSION`
   (syncs version across artifacts, regenerates Appendix A, writes the ISO draft DOCX, and prepends a section to `CHANGELOG.md`; optional `--reference-input reference/input`)
3. **Commit & tag** — once commited to `main`, create and push the tag.
