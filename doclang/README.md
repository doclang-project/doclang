# DocLang Toolkit

Official Python toolkit for working with DocLang — CLI commands and library APIs.

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
