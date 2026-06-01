# DocLang Validation

Validate DocLang XML documents against XSD schema and Schematron rules.

## Usage

```bash
# Validate a document using default bundled schemas
doclang validate document.xml

# Validate with custom schemas
doclang validate document.xml --xsd custom.xsd --sch custom.sch

# XSD validation only
doclang validate document.xml --xsd-only

# Schematron validation only
doclang validate document.xml --schematron-only

# JSON output
doclang validate document.xml --format json

# Quiet mode (exit code only)
doclang validate document.xml --quiet

# Show help
doclang --help
```

## Document Requirements

If your document doesn't declare a namespace, you can use the CLI agument `--allow-empty-namespace` (or shorthand `-n`) to automatically inject the DocLang namespace during validation:

```bash
doclang validate -n document.xml
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
