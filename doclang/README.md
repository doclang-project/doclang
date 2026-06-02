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
