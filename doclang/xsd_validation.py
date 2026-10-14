"""
DocLang XSD Validation - Business Logic

Provides XSD validation function for DocLang XML documents.
"""

import re
from pathlib import Path
from typing import Any, Union

from lxml import etree

from doclang._schemas import _bundled_xsd_path
from doclang.utils import _ensure_namespace, _parse_doclang_document, _parse_xml


def _validate_xsd_at(
    xml_file: Union[str, Path],
    xsd_file: Union[str, Path],
    allow_empty_namespace: bool = False,
    schema_version: Union[str, None] = None,
) -> list[dict[str, Any]]:
    """
    Validate XML against an XSD schema using lxml (internal).

    Args:
        xml_file: Path to XML file to validate
        xsd_file: Path to XSD schema file
        allow_empty_namespace: If True, automatically add DocLang namespace if missing
        schema_version: MAJOR.MINOR version to put in place of the document's declared version, in
            memory, before validating. Only passed for schemas that enumerate the allowed versions.
            NOTE: The bundled 0.7 schema restricts the root ``version`` attribute to
            their own version, so a document declaring any other version would otherwise be
            rejected on that attribute alone, rather than on its content.

    Returns:
        Validation errors as a list of dicts with 'line' and 'message' keys
    """
    try:
        with open(xsd_file, "rb") as f:
            # Bundled/trusted schema: hardened parse only (no DocLang DTD policy).
            schema_doc = _parse_xml(f)
            schema = etree.XMLSchema(schema_doc)

        with open(xml_file, "rb") as f:
            xml_doc = _parse_doclang_document(f)

        if allow_empty_namespace:
            xml_doc = _ensure_namespace(xml_doc)

        if schema_version is not None:
            root = xml_doc.getroot()
            declared_version = root.get("version")
            # Only well-formed versions are replaced; malformed ones are left for the schema to report.
            if declared_version is not None and re.fullmatch(r"[0-9]+\.[0-9]+", declared_version):
                root.set("version", schema_version)

        if schema.validate(xml_doc):
            return []
        return [{"line": error.line, "message": error.message} for error in schema.error_log]

    except Exception as e:
        return [{"error": str(e)}]


def _validate_xsd(
    xml_file: Union[str, Path],
    allow_empty_namespace: bool = False,
    xsd_file: Union[str, Path, None] = None,
    schema_version: Union[str, None] = None,
) -> list[dict[str, Any]]:
    """Validate XML against the given DocLang XSD schema (default: the bundled, latest one)."""
    return _validate_xsd_at(
        xml_file,
        xsd_file or _bundled_xsd_path(),
        allow_empty_namespace=allow_empty_namespace,
        schema_version=schema_version,
    )
