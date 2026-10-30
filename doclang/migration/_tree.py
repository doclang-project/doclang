"""Tree helpers shared by the migration steps (internal)."""

from __future__ import annotations

from typing import Any

from lxml import etree


def is_element(node: etree._Element) -> bool:
    """True for elements (as opposed to comments and processing instructions)."""
    return isinstance(node.tag, str)


def local_name(element: etree._Element) -> str:
    return etree.QName(element).localname


def location(element: etree._Element) -> str:
    """Path of ``element`` using local names, e.g. ``/doclang/group/track[2]``."""
    parts: list[str] = []
    node: etree._Element | None = element
    while node is not None and is_element(node):
        name = local_name(node)
        parent = node.getparent()
        if parent is not None:
            same = [s for s in parent if is_element(s) and local_name(s) == name]
            if len(same) > 1:
                name = f"{name}[{same.index(node) + 1}]"
        parts.append(name)
        node = parent
    return "/" + "/".join(reversed(parts))


def remove_keeping_tail(element: etree._Element) -> None:
    """Remove ``element`` from its parent but keep the text that follows it.

    Whitespace-only text before and after the element collapses into the text after it, so that no
    blank line is left behind.
    """
    parent = element.getparent()
    assert parent is not None
    tail = element.tail or ""
    previous = element.getprevious()
    before = (previous.tail if previous is not None else parent.text) or ""
    merged = tail if not before.strip() and not tail.strip() else before + tail
    if previous is not None:
        previous.tail = merged or None
    else:
        parent.text = merged or None
    parent.remove(element)


class Changes:
    """What a migration mapped or dropped, in document order, followed by the archive members it renamed, removed
    or orphaned."""

    def __init__(self) -> None:
        self.items: list[dict[str, Any]] = []

    def record(self, kind: str, element: etree._Element, message: str) -> None:
        """Record a change (``kind`` is "mapped" or "dropped") of ``element`` (call before changing it)."""
        self.items.append(
            {
                "kind": kind,
                "location": location(element),
                "line": element.sourceline,
                "message": message,
            }
        )

    def record_member(self, kind: str, name: str, message: str) -> None:
        """Record a change (``kind`` is "renamed", "removed" or "orphaned") of the archive member ``name``."""
        self.items.append({"kind": kind, "location": name, "line": None, "message": message})
