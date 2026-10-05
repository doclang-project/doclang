"""
Shared utility functions for DocLang validation.
"""

from pathlib import Path
from typing import BinaryIO, Protocol, Union

from lxml import etree

from doclang.version import _resolve_version

_DOCLANG_NAMESPACE = "https://www.doclang.ai/ns/v0"
_VERSION = _resolve_version()

_DTD_REJECTED_MESSAGE = "DTD declarations and entity references are not allowed in DocLang documents"


class _BinaryWriter(Protocol):
    def write(self, data: bytes, /) -> int: ...


def _safe_xml_parser() -> etree.XMLParser:
    """Return an lxml parser that does not expand entities or load external DTDs."""
    return etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        load_dtd=False,
        dtd_validation=False,
    )


def _contains_entity_nodes(node: etree._Element) -> bool:
    for child in node:
        if not isinstance(child.tag, str):
            # Comments/PIs are skipped elsewhere; treat non-element nodes as unsafe
            # when they are entity references (lxml exposes them as _Entity).
            if type(child).__name__ == "_Entity":
                return True
            continue
        if _contains_entity_nodes(child):
            return True
    return False


def _reject_dtd_or_entities(xml_doc: etree._ElementTree) -> None:
    """Fail closed if the document declares a DTD or contains entity nodes."""
    if (xml_doc.docinfo.doctype or "").strip() or _contains_entity_nodes(xml_doc.getroot()):
        raise ValueError(_DTD_REJECTED_MESSAGE)


def _parse_xml(source: Union[str, Path, BinaryIO]) -> etree._ElementTree:
    """Parse XML with :func:`_safe_xml_parser` (no DTD/entity policy checks)."""
    return etree.parse(source, parser=_safe_xml_parser())


def _parse_doclang_document(source: Union[str, Path, BinaryIO]) -> etree._ElementTree:
    """Parse a DocLang document safely and reject DTD / entity payloads."""
    xml_doc = _parse_xml(source)
    _reject_dtd_or_entities(xml_doc)
    return xml_doc


def _write_xml_without_dtd(xml_doc: etree._ElementTree, out: _BinaryWriter) -> None:
    """Serialize ``xml_doc`` without preserving any DOCTYPE / internal subset."""
    out.write(
        etree.tostring(
            xml_doc.getroot(),
            encoding="utf-8",
            xml_declaration=True,
        )
    )


def _ensure_namespace(xml_doc: etree._ElementTree) -> etree._ElementTree:
    """
    Ensure the document has the DocLang namespace.
    If the root element has no namespace, add the default DocLang namespace.

    Args:
        xml_doc: The XML document tree

    Returns:
        The XML document tree with namespace added if it was missing
    """
    root = xml_doc.getroot()

    # Check if root element has a namespace
    root_tag = str(root.tag)
    if root_tag.startswith("{"):
        # Already has a namespace
        return xml_doc

    # No namespace - add DocLang namespace
    # Create a new root with namespace
    new_root = etree.Element(f"{{{_DOCLANG_NAMESPACE}}}{root.tag}", nsmap={None: _DOCLANG_NAMESPACE})

    # Copy attributes
    for key, value in root.attrib.items():
        new_root.set(key, value)

    # Copy children recursively
    def copy_element(source, target):
        target.text = source.text
        target.tail = source.tail
        for child in source:
            # Skip comments and processing instructions
            if not isinstance(child.tag, str):
                continue

            child_tag = str(child.tag)
            if child_tag.startswith("{"):
                # Child already has namespace
                new_child = etree.SubElement(target, child_tag)
            else:
                # Add namespace to child
                new_child = etree.SubElement(target, f"{{{_DOCLANG_NAMESPACE}}}{child_tag}")

            for key, value in child.attrib.items():
                new_child.set(key, value)

            copy_element(child, new_child)

    copy_element(root, new_root)

    # Create new document with namespaced root
    new_doc = etree.ElementTree(new_root)
    return new_doc
