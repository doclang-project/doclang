# DocLang XML Schema Validation

Validate DocLang XML documents against XSD schema and Schematron rules.

## Installation

```bash
uv sync
```

## Usage

```bash
# Validate a document using default bundled schemas
uv run doclang validate document.xml

# Validate with custom schemas
uv run doclang validate document.xml --xsd custom.xsd --sch custom.sch

# XSD validation only
uv run doclang validate document.xml --xsd-only

# Schematron validation only
uv run doclang validate document.xml --schematron-only

# JSON output
uv run doclang validate document.xml --format json

# Quiet mode (exit code only)
uv run doclang validate document.xml --quiet

# Show help
uv run doclang --help
```

## Run Tests

```bash
uv run pytest
```

## Document Requirements

The DocLang XML document should include the namespace:

```xml
<doclang xmlns="https://www.doclang.ai/ns/v1" version="1.0.0">
    <!-- ... -->
</doclang>
```

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

## References

- [XSD 1.0 Specification](https://www.w3.org/TR/xmlschema-1/)
- [ISO Schematron](http://schematron.com/)
- [XPath 3.1 Specification](https://www.w3.org/TR/xpath-31/)
