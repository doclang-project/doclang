# DocLang Toolkit

Official Python toolkit for working with DocLang — CLI commands and library APIs.

This toolkit and associated schemas are meant to enable validation of DocLang documents in line with the DocLang specification. In case of discrepancies, the authoritative source is the specification.

## Installation

Recommended — full validation (XSD + Schematron):

```bash
pip install "doclang[schematron-saxon]"
```

Minimal install without Schematron (packaging, XSD-only validation, or platforms where
`saxonche` has no wheel — e.g. Windows on ARM64, ppc64le, s390x):

```bash
pip install doclang
```

On a minimal install, pass `xsd_only=True` for XSD-only validation, or supply a custom
`schematron=` backend. Default `validate()` expects a Schematron backend and raises
`SchematronBackendNotFound` when none is available.

## CLI

### Validation

```bash
doclang validate my_document.dclg
```

The schema is chosen as follows:

1. `--spec-version X.Y` (Python: `spec_version="X.Y"`) uses the bundled schema of that version, overriding the
   document's own. It is an error if there is none.
2. Otherwise the spec version in the `version` attribute of the document's root element is used.
3. Otherwise the latest schema (the development head) is used, with a warning. This covers documents that
   declare no version, and (with a warning naming the version) documents whose declared version has no bundled
   schema. Pass `--strict-declared-version` (Python: `strict_declared_version=True`) to fail in the latter case.

The latest released schema of each spec minor version is bundled in `doclang/schemas/<MAJOR.MINOR>/`.
The schema directly in `doclang/` is the development head.

> **Note on 0.7:** the 0.7 XSD only accepts `0.7` in the root `version` attribute (later versions only
> require the `MAJOR.MINOR` format). So that a document declaring another version (e.g. `0.8`) can be
> checked against the 0.7 rules, the toolkit by default replaces the declared `version` with `0.7` in
> memory for XSD validation (the file is not modified), and says so in a note. The declared version itself
> is then not checked; all other 0.7 rules are still checked. Use `--strict-xsd-version-attr` (Python:
> `strict_xsd_version_attr=True`) to apply the XSD's version check as is, in which case such a document fails.

#### More validation scenarios

```bash
## Inject DocLang namespace if document doesn't declare it:
doclang validate my_document.dclg --allow-empty-namespace

# XSD validation only
doclang validate my_document.dclg --xsd-only

# Schematron validation only
doclang validate my_document.dclg --schematron-only

# JSON output
doclang validate my_document.dclg --format json

# Validate against a specific spec version (overrides the document's `version`)
doclang validate my_document.dclg --spec-version 0.7

# ... and apply the XSD's own `version` attribute check as is
doclang validate my_document.dclg --spec-version 0.7 --strict-xsd-version-attr

# Quiet mode (exit code only)
doclang validate my_document.dclg --quiet

# Show help
doclang --help
```

### Packaging

```bash
doclang pack markup.dclg
```

#### More packaging scenarios

```bash
doclang pack markup.dclg -o report.dclx
doclang pack markup.dclg --pages screenshots/
doclang pack markup.dclg --page a.png --page b.png
doclang pack markup.dclg --asset chart.svg=exports/diagram.svg
doclang pack markup.dclg --assets payload/
doclang pack markup.dclg --validate
```

### Migration

Migrate a document to a specific spec version:

```bash
doclang migrate document.dclg --to 0.7
```

The migrated document goes to stdout (or `-o FILE`); what was changed goes to stderr. Migrating to an older version
is best effort: content that has an equivalent in the target version is mapped (e.g. additional captions become
`<text>`), the rest is dropped (e.g. `<track>`), and every change is reported with its location. Migrating to a
newer version rewrites the document where the newer version reads the same markup differently, so that it keeps
its meaning; otherwise only the `version` attribute changes, as documents are forward compatible.

The source version is the document's `version` attribute. A document without one is read as the latest version,
with a warning; `--from X.Y` reads it as version X.Y instead (a document that declares another version is an
error).

#### More migration scenarios

```bash
doclang migrate document.dclg --to 0.7 -o document_0.7.dclg
doclang migrate document.dclg --to 0.7 --strict        # fail instead of changing anything
doclang migrate undeclared.dclg --from 0.8 --to 0.9    # a document without a version attribute, written for 0.8
doclang migrate document.dclg --to 0.7 --format json   # versions, changes and the document as JSON
doclang migrate document.dclg --to 0.7 --input-validation xsd --output-validation xsd   # without Schematron
doclang migrate document.dclg --to 0.7 --input-validation none                          # skip validating the input
```

By default the document is validated before the migration (against its own version) and the result afterwards
(against the target version), in full, XSD and Schematron. `--input-validation` and `--output-validation` take
`all`, `xsd`, `schematron` or `none`; `xsd` and `schematron` mean the same as `--xsd-only` and `--schematron-only`
of `doclang validate`. As there, Schematron needs a backend (see [Installation](#installation)): without one,
`doclang migrate` fails and tells you so, and you opt out explicitly, e.g. with the `xsd` scope for both.

## Python API

### Validation

```python
from doclang import validate, ValidationError

try:
    validate("my_document.dclg")
    print("Validation OK (no exception)")
except ValidationError as exc:
    print(exc)  # human-readable summary
    print(f"{exc.xsd_errors=}")
    print(f"{exc.schematron_errors=}")
```

### Custom Schematron backends

DocLang does not bundle a single Schematron runtime in the core package. Instead,
`validate()` accepts an optional Schematron engine via the `schematron` parameter.
When omitted, the default Saxon/C backend is used (requires `doclang[schematron-saxon]`).

To plug in your own engine, implement the `SchematronValidator` protocol and return
`SchematronViolation` objects — one per failed rule:

```python
from pathlib import Path

from doclang import SchematronViolation, validate


class MySchematronValidator:
    def validate(
        self,
        xml_path: Path,
        *,
        schema_path: Path,
        allow_empty_namespace: bool = False,
    ) -> list[SchematronViolation]:
        # Run your engine against schema_path (bundled doclang.sch) and xml_path.
        # Map failures to SchematronViolation(location=..., message=...).
        ...

validate("my_document.dclg", schematron=MySchematronValidator())
```

Notes for implementers:

- `schema_path` points at the bundled `doclang.sch` rules (XPath 3.1 / `queryBinding="xslt3"`).
- Set `allow_empty_namespace=True` when the XML may lack the DocLang namespace; the
  default Saxon backend injects it before validation — custom backends should do the same
  if they operate on file paths rather than pre-processed trees.
- Use `xsd_only=True` on `validate()` when your application does not need Schematron at all.

**Example:** [pyschematron](https://pypi.org/project/pyschematron/) is a pure-Python
Schematron evaluator you can wrap in a `SchematronValidator` and install separately in
your own project (doclang does not ship or endorse it as a dependency). Similar adapters
can be built for any engine that evaluates ISO Schematron or consumes a precompiled XSLT
stylesheet derived from `doclang.sch`.

### Packaging

```python
from doclang import pack, PackagingError

path = pack(
    "markup.dclg",
    pages="screenshots/",
    assets={"chart.svg": "exports/diagram.svg"},
)
print(f"Created {path}")
```

### Migration

```python
from doclang import migrate, MigrationError

try:
    result = migrate("document.dclg", to="0.7")
except MigrationError as exc:
    print(exc)
else:
    print(result.xml)  # the migrated document
    for change in result.changes:  # {"kind": "mapped" | "dropped", "location": ..., "line": ..., "message": ...}
        print(change["kind"], change["location"])
```

`migrate(..., strict=True)` raises `MigrationError` (carrying `changes`) if anything would be changed. The source
version is the document's `version` attribute; without one the document is treated as the latest version, with a
warning.

The input is validated before and the result after the migration; `input_validation` and `output_validation`
(`"all"` by default, or `"xsd"`, `"schematron"`, `"none"`) select what runs. As with `validate()`, a missing
Schematron backend raises `SchematronBackendNotFound`. An invalid input raises `MigrationError`; so does an invalid
result, which indicates a bug in a migration step (or an invalid input that was not validated).

## Validation Rules

### XSD Validation (doclang.xsd)

Standard XML Schema Definition for structural validation:

- Document structure and element hierarchy
- Data types and attributes
- Element ordering

### Schematron Rules (doclang.sch)

Additional business rules that XSD cannot express, using XSLT 3.0 and XPath 3.1:

```xml
<sch:pattern id="my-rule">
  <sch:rule context="dl:element">
    <sch:assert test="condition">Error message</sch:assert>
  </sch:rule>
</sch:pattern>
```

The bundled Saxon/C backend transpiles these rules to XSLT 3.0 at validation time.
Alternative backends may evaluate the same `.sch` file directly or use a precompiled
`.xsl` artifact if their runtime requires it.

## XSD Validation with VS Code

In VS Code you can use [Red Hat's XML extension](https://open-vsx.org/vscode/item?itemName=redhat.vscode-xml) and enable IDE-native XSD validation by adding the following to your `settings.json` (ℹ️ replacing the actual XSD path):

```xml
    "xml.fileAssociations": [
        {
            "pattern": "**/*.dclg",
            "systemId": "file:///absolute/path/to/doclang.xsd",
        }
    ],
```

For this to work, the DocLang XML document must include the relevant namespace:

```xml
<doclang xmlns="https://www.doclang.ai/ns/v0">
    <!-- ... -->
</doclang>
```

Note that this approach does not cover Schematron validation rules.

## References

- [XSD 1.0 Specification](https://www.w3.org/TR/xmlschema-1/)
- [ISO Schematron](http://schematron.com/)
- [XPath 3.1 Specification](https://www.w3.org/TR/xpath-31/)
