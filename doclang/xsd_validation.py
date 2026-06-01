"""
DocLang XSD Validation - Business Logic

Provides XSD validation function for DocLang XML documents.
This module is a sibling to schematron_validator.py, with routing handled by cli.py.
"""

from pathlib import Path
from typing import Any, Union

from lxml import etree

from doclang.utils import _ensure_namespace


def _validate_xsd(
    xml_file: Union[str, Path], xsd_file: Union[str, Path], allow_empty_namespace: bool = False
) -> tuple[bool, list[dict[str, Any]]]:
    """
    Validate XML against XSD schema using lxml.

    Pure validation logic without any output formatting.

    Args:
        xml_file: Path to XML file to validate
        xsd_file: Path to XSD schema file
        allow_empty_namespace: If True, automatically add DocLang namespace if missing

    Returns:
        Tuple of (is_valid, errors) where errors is a list of dicts with 'line' and 'message' keys
    """
    try:
        # Parse XSD
        with open(xsd_file, "rb") as f:
            schema_doc = etree.parse(f)
            schema = etree.XMLSchema(schema_doc)

        # Parse XML
        with open(xml_file, "rb") as f:
            xml_doc = etree.parse(f)

        # Optionally ensure namespace is present
        if allow_empty_namespace:
            xml_doc = _ensure_namespace(xml_doc)

        # Validate
        if schema.validate(xml_doc):
            return True, []
        else:
            errors = [{"line": error.line, "message": error.message} for error in schema.error_log]
            return False, errors

    except Exception as e:
        return False, [{"error": str(e)}]
