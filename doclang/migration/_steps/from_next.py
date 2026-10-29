"""Steps from the development head to the newest released spec version (internal).

Every addition to the head schema that the previous version cannot express adds its rule here.
At release, ``utils/prepare_release.py`` renames this module to ``v<new>_to_<previous>.py`` and
creates a fresh, empty one. Do not mention version numbers in the messages for that reason.
"""

from __future__ import annotations

from lxml import etree

from doclang.migration._tree import Changes, is_element, local_name

_WHITESPACE = " \t\r\n"
_FORMATTING = frozenset("bold italic underline strikethrough superscript subscript handwriting rtl".split())


def migrate(root: etree._Element, changes: Changes) -> None:
    _move_content_out_of_field_headings(root, changes)


def _move_content_out_of_field_headings(root: etree._Element, changes: Changes) -> None:
    """<field_heading> cannot hold <content> in the target: a <content> goes into the formatting element next to it
    (with only whitespace between them), at its end or start; without one, it is unwrapped into raw text."""
    headings = [e for e in root.iter() if is_element(e) and local_name(e) == "field_heading"]
    for heading in headings:
        for content in [c for c in heading if is_element(c) and local_name(c) == "content"]:
            previous, following = content.getprevious(), content.getnext()
            if _formatting(previous) and not (previous.tail or "").strip(_WHITESPACE):
                changes.record(
                    "mapped", content, "<content> moved into a formatting element, as <field_heading> cannot hold it"
                )
                gap, tail = previous.tail or "", content.tail
                if len(previous):
                    previous[-1].tail = (previous[-1].tail or "") + gap or None
                else:
                    previous.text = (previous.text or "") + gap or None
                previous.append(content)
                content.tail, previous.tail = None, tail
            elif _formatting(following) and not (content.tail or "").strip(_WHITESPACE):
                changes.record(
                    "mapped", content, "<content> moved into a formatting element, as <field_heading> cannot hold it"
                )
                gap, text = content.tail or "", following.text
                following.text = None
                following.insert(0, content)
                content.tail = gap + (text or "") or None
            else:
                changes.record("dropped", content, "<content> unwrapped, as <field_heading> cannot hold it")
                text = (content.text or "") + (content.tail or "")
                if previous is not None:
                    previous.tail = (previous.tail or "") + text or None
                else:
                    heading.text = (heading.text or "") + text or None
                heading.remove(content)


def _formatting(element: etree._Element | None) -> bool:
    return element is not None and is_element(element) and local_name(element) in _FORMATTING
