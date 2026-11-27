"""Tree helpers for the normalization rules: text slots of mixed content and edits to them (internal).

Raw text in lxml lives in two places: ``element.text`` (before the first child) and ``child.tail`` (after a child,
inside its parent). A *slot* names one of them as ``(element, "text")`` or ``(child, "tail")``; the slot's *host* is
the element whose content the text is part of (``element`` or the parent of ``child``).
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from typing import Literal

from lxml import etree

from doclang.migration._tree import is_element, local_name

Attr = Literal["text", "tail"]
Slot = tuple[etree._Element, Attr]

FORMATTING = frozenset(
    {"bold", "italic", "strikethrough", "underline", "superscript", "subscript", "rtl", "handwriting"}
)

# Elements whose raw text may be followed by a <formula> (and by formatting): "semantic" content models.
FORMULA_HOSTS = frozenset(
    {
        "text",
        "heading",
        "caption",
        "page_header",
        "page_footer",
        "footnote",
        "marker",
        "field_region",
        "field_heading",
        "field_item",
        "key",
        "value",
        "list",
        "table",
        "tabular",
        "index",
        "voice",
        "chapter",
    }
)

# Elements whose raw text may be followed by formatting (<superscript>, ...) but not by a <formula>.
SCRIPT_HOSTS = FORMULA_HOSTS | FORMATTING | {"hint", "track"}

# Elements whose content is not prose: math, code and arbitrary metadata.
NOT_PROSE = frozenset({"formula", "code", "head", "meta", "custom"})


def name(element: etree._Element) -> str:
    return local_name(element) if is_element(element) else ""


def block(element: etree._Element) -> etree._Element:
    """The nearest ancestor-or-self of ``element`` that is not formatting, a hint or ``<content>``."""
    node = element
    while name(node) in FORMATTING | {"hint", "content"}:
        parent = node.getparent()
        if parent is None:
            break
        node = parent
    return node


def in_prose(host: etree._Element) -> bool:
    """Whether raw text of ``host`` is prose (as opposed to formula, code or metadata content)."""
    if name(block(host)) in NOT_PROSE:
        return False
    node: etree._Element | None = host
    while node is not None:
        if name(node) in {"head", "meta", "custom"}:
            return False
        node = node.getparent()
    return True


def get(slot: Slot) -> str:
    element, attr = slot
    return (element.text if attr == "text" else element.tail) or ""


def put(slot: Slot, value: str) -> None:
    """Set the text of ``slot``; the text of a ``<content>`` written as CDATA stays CDATA."""
    element, attr = slot
    if attr == "text":
        cdata = name(element) == "content" and bool(element.text) and is_cdata(element)
        element.text = etree.CDATA(value) if cdata and value else (value or None)
    else:
        element.tail = value or None


def host(slot: Slot) -> etree._Element:
    element, attr = slot
    if attr == "text":
        return element
    parent = element.getparent()
    assert parent is not None
    return parent


def prose_slots(root: etree._Element) -> list[Slot]:
    """All slots with prose text, in document order (a snapshot: edits do not change it)."""
    slots: list[Slot] = []
    for element in root.iter():
        if not is_element(element):
            if element.tail and element.getparent() is not None and in_prose(element.getparent()):
                slots.append((element, "tail"))
            continue
        if element.text and in_prose(element):
            slots.append((element, "text"))
        parent = element.getparent()
        if element.tail and parent is not None and in_prose(parent):
            slots.append((element, "tail"))
    return slots


def before(element: etree._Element) -> Slot:
    """The slot holding the text right before ``element``."""
    previous = element.getprevious()
    if previous is not None:
        return (previous, "tail")
    parent = element.getparent()
    assert parent is not None
    return (parent, "text")


def new_element(parent: etree._Element, local: str, text: str | None = None) -> etree._Element:
    """A new ``local`` element in the namespace of ``parent``, appended to ``parent`` (move it afterwards).

    Creating it inside the tree keeps the namespace declarations of the document (no ``ns0:`` prefixes).
    """
    namespace = etree.QName(parent).namespace
    element = etree.SubElement(parent, f"{{{namespace}}}{local}" if namespace else local)
    element.text = text
    return element


def insert_after(slot: Slot, element: etree._Element) -> None:
    """Move ``element`` to just after the text of ``slot``."""
    owner, attr = slot
    if attr == "text":
        owner.insert(0, element)
    else:
        parent = owner.getparent()
        assert parent is not None
        parent.insert(parent.index(owner) + 1, element)


def wrap_span(slot: Slot, start: int, end: int, local: str, content: str) -> etree._Element:
    """Replace ``[start, end)`` of the text of ``slot`` with a new ``local`` element holding ``content``."""
    text = get(slot)
    element = new_element(host(slot), local, content)
    put(slot, text[:start])
    element.tail = text[end:] or None
    insert_after(slot, element)
    return element


def replace_with_text(element: etree._Element, text: str) -> None:
    """Remove ``element`` (and its content), putting ``text`` and its tail in its place."""
    slot = before(element)
    put(slot, get(slot) + text + (element.tail or ""))
    parent = element.getparent()
    assert parent is not None
    parent.remove(element)


def replace_with(element: etree._Element, replacement: etree._Element) -> None:
    """Put ``replacement`` where ``element`` is; the tail stays."""
    replacement.tail = element.tail
    parent = element.getparent()
    assert parent is not None
    parent.replace(element, replacement)


def plain_text(element: etree._Element) -> str | None:
    """The text of ``element`` if it has no children (comments included), else None."""
    if len(element):
        return None
    return element.text or ""


def is_cdata(element: etree._Element) -> bool:
    """Whether the text of ``element`` is written as a CDATA section."""
    return b"<![CDATA[" in etree.tostring(element, with_tail=False)


def iter_named(root: etree._Element, local: str) -> Iterator[etree._Element]:
    """Elements named ``local`` (any namespace), as a snapshot."""
    return iter([e for e in root.iter() if is_element(e) and local_name(e) == local])


def markup(element: etree._Element) -> str:
    """``element`` as markup without namespace declarations and tail, for change messages."""
    text = etree.tostring(element, with_tail=False, encoding="unicode")
    return _strip_namespaces(text)


def _strip_namespaces(text: str) -> str:
    return re.sub(r'\s+xmlns(:\w+)?="[^"]*"', "", text)
