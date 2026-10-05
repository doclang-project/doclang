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

### Writing and editing documents

```python
from doclang import (
    DoclangDocument,
    DoclangPictureNode,
    DoclangTableNode,
    DoclangTextNode,
)

doc = DoclangDocument.empty()
first = doc.append_child("/doclang[1]", DoclangTextNode("Introduction"))
doc.insert_after(first, DoclangTextNode("Measurements"))

table = DoclangTableNode(rows=2, columns=2)
table.set_caption("Results")
table.append_to_cell(0, 0, DoclangTextNode("42"))
table.append_to_cell(0, 1, DoclangPictureNode("assets/plot.png"))
doc.append_child("/doclang[1]", table)

valid, error = doc.is_valid()
assert valid, error
xml = doc.xml()
```

`append_child` and `prepend_child` take a parent XPath. `insert_before` and
`insert_after` take an existing sibling XPath. `delete` removes an element at
its XPath. Each inserted node is copied into the document; editing the detached
node later does not change the document. Validation runs only when requested.
Named nodes also provide `is_valid()` for local checks and
`is_valid_in(document, InsertionSite.append_child(...))` for a proposed edit.

`DocLangXDocument` inherits these edits. After editing an archive with
annotations, `write()` reports that annotation XPath values may be stale.
Review them before calling `write(path, allow_stale_annotations=True)`.

Both `DoclangDocument` and `DoclangXDocument` expose the root specification
version as a comparable `DoclangVersion`:

```python
from doclang import DoclangVersion, ElementTag, OtslToken, xml_name

assert doc.version() >= DoclangVersion.parse("0.6")
assert xml_name(ElementTag.table) == "table"
assert xml_name(OtslToken.fc) == "fcel"
```

The version comes from the root `version` attribute, with the schema default
of `0.7` when it is absent. A document without a parsed root returns `None`.
Ordering compares the numeric major and minor components; it does not claim
schema compatibility between `0.x` versions.

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

Native document validation is explicit: callers can assemble or edit a document
before requesting a validation report.

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
# Native DCLX editing and package access

The feature-branch native API exposes `DoclangDocument` for DocLang XML and
`DoclangXDocument` (also exported as `DocLangXDocument`) for DCLX packages.
`DoclangXDocument.read_bytes()` and `write_bytes()` operate on complete DCLX
archives in memory; `read()` and `write()` operate on files. Both read methods
accept optional `ArchiveLimits`. The default limits are 256 MiB compressed,
10,000 entries, 256 MiB per uncompressed entry, 1 GiB total uncompressed,
and a compression ratio of 200. ZIP entries are checked before extraction;
parts are decompressed when requested. The compressed archive is retained in
memory while the document is open.

```python
from doclang import ArchiveLimits, DoclangDocument, DoclangXDocument

doc = DoclangXDocument()
assert doc.read_xml('<doclang version="0.7"><text>Hello</text></doclang>')
doc.set_document_summary('<doclang><text>Short summary</text></doclang>')
doc.set_part_text("context/source.json", '{"kind":"example"}', "application/json")
payload = doc.write_bytes()

copy = DoclangXDocument()
limits = ArchiveLimits()
assert copy.read_bytes(payload, limits)
assert copy.get_part_text("context/source.json") == '{"kind":"example"}'
assert copy.validate_package()["ok"]
```

`get_part_bytes`, `get_part_text`, `set_part_bytes`, `set_part_text`, and
`remove_part` use archive-relative paths. Generic setters reject the main
document, OPC metadata, and DocLang-managed `annotations/` paths. Setters
require an explicit content type and update `[Content_Types].xml`; `write`
also supplies declarations for parts carried over from an existing archive.
Unknown parts survive read/write unless removed. `validate_package()` returns
`{"ok": bool, "errors": [{"code", "path", "message"}, ...]}` and checks
the document, TOC targets, staleness, OPC metadata, and part declarations.
Legacy DCLX files without OPC metadata can still be read; writing them adds
the missing declarations and document relationship.

The XML-side `iter_nodes(xpath=None, limit=1000)` returns bounded records with
`xpath`, `parent_xpath`, `name`, `text`, `page`, and `bbox`. XPaths address a
particular document revision: structural edits can shift them. A document edit
marks existing annotations and sidecars stale. Writes refuse stale data by
default; repair or clear it first. The explicit `allow_stale_annotations` and
`allow_stale_sidecars` flags permit a reviewed override, though unresolved TOC
targets always block a write.
