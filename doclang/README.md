# DocLang Toolkit

Official Python toolkit for working with DocLang — CLI commands and library APIs.

## Installation

```bash
pip install doclang
```

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

The validation uses XSLT 3.0 for modern XPath features.

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
