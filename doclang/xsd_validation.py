"""
DocLang XSD Validation - Business Logic

Provides XSD validation function for DocLang XML documents.
"""

from pathlib import Path
from typing import Any, Union

from lxml import etree

from doclang._schemas import _bundled_xsd_path
from doclang.utils import _ensure_namespace


def _validate_xsd_at(
    xml_file: Union[str, Path], xsd_file: Union[str, Path], allow_empty_namespace: bool = False
) -> list[dict[str, Any]]:
    """
    Validate XML against an XSD schema using lxml (internal).

    Args:
        xml_file: Path to XML file to validate
        xsd_file: Path to XSD schema file
        allow_empty_namespace: If True, automatically add DocLang namespace if missing

    Returns:
        Validation errors as a list of dicts with 'line' and 'message' keys
    """
    try:
        with open(xsd_file, "rb") as f:
            schema_doc = etree.parse(f)
            schema = etree.XMLSchema(schema_doc)

        with open(xml_file, "rb") as f:
            xml_doc = etree.parse(f)

        if allow_empty_namespace:
            xml_doc = _ensure_namespace(xml_doc)

        if schema.validate(xml_doc):
            return []
        return [{"line": error.line, "message": error.message} for error in schema.error_log]

    except Exception as e:
        return [{"error": str(e)}]


def _validate_xsd(xml_file: Union[str, Path], allow_empty_namespace: bool = False) -> list[dict[str, Any]]:
    """Validate XML against the bundled DocLang XSD schema."""
    return _validate_xsd_at(xml_file, _bundled_xsd_path(), allow_empty_namespace=allow_empty_namespace)
