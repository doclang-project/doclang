# DocLang XML Schema Validation

Validate DocLang XML documents against XSD schema and Schematron rules.

## Installation

Install the package using pip or uv:

```bash
pip install doclang
# or
uv pip install doclang
```

The schemas (XSD and Schematron) are bundled with the package, so you can start validating immediately after installation.

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

## Run Tests

```bash
pytest
```

## Document Requirements

Your DocLang XML document must include the namespace:

```xml
<doclang xmlns="https://www.doclang.ai/ns/v1" version="1.0.0">
    <!-- your content -->
</doclang>
```

**Optional:** If your document doesn't declare a namespace, you can use the `--allow-empty-namespace` (or `-n`) flag to automatically inject the DocLang namespace during validation:

```bash
doclang validate document.xml --allow-empty-namespace
# or shorter:
doclang validate document.xml -n
```

## Validation Rules

### XSD Validation (doclang.xsd)
- Document structure and element hierarchy
- Data types and attributes
- Element ordering

### Schematron Validation (doclang.sch)
Additional business rules using XSLT 3.0:

1. **Hyperlink URI Position**: Text before `<uri>` must be whitespace-only
   ```xml
   <!-- Valid -->
   <hyperlink><uri>https://example.com</uri>link text</hyperlink>

   <!-- Invalid -->
   <hyperlink>text before<uri>https://example.com</uri></hyperlink>
   ```

2. **Floating Group Content**: `floating_group` elements must contain appropriate content based on their `class` attribute

## For Schema Developers

### XSD Schema (doclang.xsd)
Standard XML Schema Definition for structural validation.

### Schematron Rules (doclang.sch)
Business rules that XSD cannot express, using XSLT 3.0 and XPath 3.1:

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
