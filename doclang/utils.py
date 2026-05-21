"""
Shared utility functions for DocLang validation.
"""

from lxml import etree

from doclang.version import resolve_version

_DOCLANG_NAMESPACE = "https://www.doclang.ai/ns/v0"
_VERSION = resolve_version()


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
