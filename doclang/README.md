# DocLang Validation

Validate DocLang XML documents against XSD schema and Schematron rules.

## Installation

```bash
pip install doclang
```

## Usage

### Basic CLI Usage

```bash
doclang validate my_document.dclg.xml
```

### More CLI Usage Scenarios

```bash
## Inject DocLang namespace if document doesn't declare it:
doclang validate my_document.dclg.xml --allow-empty-namespace

# XSD validation only
doclang validate my_document.dclg.xml --xsd-only

# Schematron validation only
doclang validate my_document.dclg.xml --schematron-only

# JSON output
doclang validate my_document.dclg.xml --format json

# Quiet mode (exit code only)
doclang validate my_document.dclg.xml --quiet

# Show help
doclang --help
```

### Python API

```python
from doclang import validate, ValidationError

try:
    validate("my_document.dclg.xml")
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
of `0.6` when it is absent. A document without a parsed root returns `None`.
Ordering compares the numeric major and minor components; it does not claim
schema compatibility between `0.x` versions.

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

The Python package evaluates these rules in its native backend. Validation is
separate from document editing, so callers can assemble a document before
checking it.

## XSD Validation with VS Code

In VS Code you can use [Red Hat's XML extension](https://open-vsx.org/vscode/item?itemName=redhat.vscode-xml) and enable IDE-native XSD validation by adding the following to your `settings.json` (ℹ️ replacing the actual XSD path):

```xml
    "xml.fileAssociations": [
        {
            "pattern": "**/*.dclg.xml",
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
