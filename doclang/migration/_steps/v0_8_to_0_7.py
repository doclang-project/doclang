"""Steps from spec version 0.8 to 0.7 (internal)."""

from __future__ import annotations

from lxml import etree

from doclang.migration._tree import Changes, is_element, local_name, remove_keeping_tail


def migrate(root: etree._Element, changes: Changes) -> None:
    _drop_tracks(root, changes)
    _split_multiple_captions(root, changes)


def _drop_tracks(root: etree._Element, changes: Changes) -> None:
    """<track> (and everything in it) has no equivalent in the previous version."""
    for element in list(root.iter()):
        if not is_element(element) or local_name(element) != "track":
            continue
        if any(local_name(a) == "track" for a in element.iterancestors()):
            continue  # removed together with its outermost track
        changes.record("dropped", element, "<track> has no equivalent in the target version and was removed")
        remove_keeping_tail(element)


def _split_multiple_captions(root: etree._Element, changes: Changes) -> None:
    """The previous version allows one caption per element head: the first stays, the others become <text>."""
    for element in list(root.iter()):
        if not is_element(element):
            continue
        captions = [c for c in element if is_element(c) and local_name(c) == "caption"]
        parent = element.getparent()
        if len(captions) < 2 or parent is None:
            continue
        for caption in captions[1:]:  # record first: moving captions shifts the positions of the others
            changes.record(
                "mapped",
                caption,
                f"additional <caption> converted to <text> after its parent <{local_name(element)}>; "
                "the target version allows one caption per element head",
            )
        separator = element.tail
        element.tail = None
        anchor = element
        for caption in captions[1:]:
            element.remove(caption)
            namespace = etree.QName(caption).namespace
            caption.tag = f"{{{namespace}}}text" if namespace else "text"
            caption.tail = None
            anchor.addnext(caption)
            anchor.tail = separator  # what followed the element now separates it from the moved captions
            anchor = caption
        anchor.tail = separator
