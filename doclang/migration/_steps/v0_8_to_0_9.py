"""Steps from spec version 0.8 to 0.9 (internal)."""

from __future__ import annotations

import re

from lxml import etree

from doclang.migration._tree import Changes, is_element, local_name

_WHITESPACE = " \t\r\n"

# The target's terms, as of this step (kept here, so that the step does not change with later versions):
# elements whose body allows raw text, and those that hold it only in a virtual <text> (list items, table cells) or
# as the spoken text of transcript turns. An element allowing raw text is inline in the body of one of them, unless it
# is a head element or sits outside the spoken text of a turn.
_RAW_TEXT = frozenset(
    "text heading footnote page_header page_footer formula code marker field_heading key value hint caption "
    "description summary classification content bold italic underline strikethrough superscript subscript "
    "handwriting rtl voice chapter".split()
)
_VIRTUAL_TEXT = frozenset("list table index tabular track".split())
_NEVER_INLINE = frozenset("caption description summary voice chapter".split())
# semantic elements that allow raw text, and the text-level elements that make a list item or cell a virtual <text>
_SEMANTIC = frozenset(
    "text heading footnote page_header page_footer formula code field_heading key value marker hint".split()
)
_TEXT_LEVEL = frozenset(
    "content bold italic underline strikethrough superscript subscript handwriting rtl checkbox".split()
)
_HEAD = frozenset("label thread h_thread xref href layer location caption description summary custom".split())
# delimiters of list items, table cells and transcript turns, and the parts of a cue block outside its turns
_DELIMITERS = frozenset(
    "ldiv fcel ecel ched rhed corn srow lcel ucel xcel nl bdiv hours minutes seconds msecs voice chapter frame audio "
    "cover".split()
)
_ONLY_SINGLE_SPACES = re.compile(r"^[^\t\r\n]*$")


def migrate(root: etree._Element, changes: Changes) -> None:
    _strip_texts(root)
    _unwrap_contents(root)


def _strip_texts(root: etree._Element) -> None:
    """Whitespace outside <content> now reads as a single space, also across inline tags; before, the spec only
    guaranteed whitespace within <content>. The previous version is read as guaranteed: every text outside
    <content> is stripped, and the pieces are joined directly. So strip the whitespace that the target would read
    as a space, i.e. next to inline tags; the target reads the rest the same. A document that relied on other
    whitespace (e.g. a space before an inline tag) may get words joined.

    Whitespace that the target ignores stays, to keep the layout: in elements without raw text, around the element
    head, at the start and end of a body, and around the delimiters of list items, table cells and transcript
    turns. So does whitespace between words, which the target reads as one space.
    """
    for element in root.iter():
        if not is_element(element) or _in_content(element):
            continue  # the text of a comment or processing instruction is its own
        if local_name(element) not in _RAW_TEXT and local_name(element) not in _VIRTUAL_TEXT:
            continue  # its whitespace is ignored
        children = list(element)
        slots = [(element, "text", None, children[0] if children else None)]
        slots += [(c, "tail", c, children[i + 1] if i + 1 < len(children) else None) for i, c in enumerate(children)]
        for node, attribute, before, after in slots:
            text = getattr(node, attribute)
            if not text:
                continue
            keep_start = _ignored_next_to(element, before, children)
            keep_end = _ignored_next_to(element, after, children)
            if not text.strip(_WHITESPACE):
                text = text if keep_start or keep_end else ""
            else:
                text = text if keep_start else text.lstrip(_WHITESPACE)
                text = text if keep_end else text.rstrip(_WHITESPACE)
            if text != getattr(node, attribute):  # an unchanged text keeps its form, e.g. a CDATA section
                setattr(node, attribute, text or None)


def _ignored_next_to(element: etree._Element, neighbour: etree._Element | None, children: list) -> bool:
    """Whether the target ignores whitespace in ``element``'s body next to ``neighbour`` (None: the start or end
    of the body)."""
    if local_name(element) in _VIRTUAL_TEXT:
        if neighbour is None or not is_element(neighbour):
            return neighbour is None
        return local_name(neighbour) in _DELIMITERS | _HEAD or not _in_virtual_text(neighbour)
    if _inline(element):
        return False  # its whitespace continues outside
    if neighbour is None:
        return True
    if not is_element(neighbour) or local_name(neighbour) not in _HEAD:
        return False
    return all(is_element(c) and local_name(c) in _HEAD for c in children[: children.index(neighbour)])


def _unwrap_contents(root: etree._Element) -> None:
    """Spaces next to tags no longer need <content>: unwrap each <content> that the target reads the same as plain
    text. That is, its text has no whitespace but single spaces, and a space at its start or end has a character
    other than whitespace next to it in the same body (else the target would drop or merge it)."""
    unwrappable = [
        c
        for c in root.iter()
        if is_element(c) and local_name(c) == "content" and _inline(c) and _reads_the_same_unwrapped(c)
    ]
    for content in unwrappable:  # decided first: unwrapping does not change the characters around the others
        _unwrap(content)


def _reads_the_same_unwrapped(content: etree._Element) -> bool:
    text = content.text or ""
    if len(content) or not text or "  " in text or not _ONLY_SINGLE_SPACES.match(text):
        return False
    if text.startswith(" ") and not _is_word_character(_character_before(content)):
        return False
    return not text.endswith(" ") or _is_word_character(_character_after(content))


def _is_word_character(character: str | None) -> bool:
    return character is not None and character not in _WHITESPACE


def _inline(element: etree._Element) -> bool:
    parent = element.getparent()
    return (
        is_element(element)
        and parent is not None
        and local_name(element) in _RAW_TEXT
        and local_name(element) not in _NEVER_INLINE
        and (
            local_name(parent) in _RAW_TEXT
            or (
                local_name(parent) in _VIRTUAL_TEXT
                and (local_name(element) not in _SEMANTIC or _in_virtual_text(element))
            )
        )
        and not any(local_name(a) == "head" for a in element.iterancestors())
    )


def _in_virtual_text(element: etree._Element) -> bool:
    """Whether ``element``, in a list item, a cell or a transcript turn, is part of a virtual <text>: the item or
    cell has raw text or text-level elements of its own. Otherwise, e.g. for two <text> paragraphs, its elements are
    blocks of their own."""
    parent = element.getparent()
    assert parent is not None
    if local_name(parent) == "track":
        return True
    siblings = list(parent)
    start = end = siblings.index(element)
    while start > 0 and not (is_element(siblings[start - 1]) and local_name(siblings[start - 1]) in _DELIMITERS):
        start -= 1
    while end + 1 < len(siblings) and not (
        is_element(siblings[end + 1]) and local_name(siblings[end + 1]) in _DELIMITERS
    ):
        end += 1
    item = siblings[start : end + 1]
    texts = [siblings[start - 1].tail if start > 0 else parent.text] + [n.tail for n in item]
    return any((t or "").strip(_WHITESPACE) for t in texts) or any(
        is_element(n) and local_name(n) in _TEXT_LEVEL for n in item
    )


def _character_before(element: etree._Element) -> str | None:
    """The character before ``element`` in its body, across inline tags; None at a boundary of the body."""
    node = element
    while True:
        previous = node.getprevious()
        parent = node.getparent()
        assert parent is not None
        text = previous.tail if previous is not None else parent.text
        if text:
            return text[-1]
        if previous is None:
            if not _inline(parent):
                return None
            node = parent
        elif _inline(previous):
            last = _last_character(previous)
            if last is not None:
                return last
            node = previous
        else:
            return None  # e.g. a head element, a list or cell delimiter, a comment


def _character_after(element: etree._Element) -> str | None:
    """The character after ``element`` in its body, across inline tags; None at a boundary of the body."""
    node = element
    while True:
        if node.tail:
            return node.tail[0]
        following = node.getnext()
        if following is None:
            parent = node.getparent()
            if parent is None or not _inline(parent):
                return None
            node = parent
        elif _inline(following):
            first = _first_character(following)
            if first is not None:
                return first
            node = following
        else:
            return None


def _last_character(element: etree._Element) -> str | None:
    """The last character within the inline ``element``; None if it has none or ends with a boundary."""
    for child in reversed(element):
        if child.tail:
            return child.tail[-1]
        if not _inline(child):
            return None
        last = _last_character(child)
        if last is not None:
            return last
    return element.text[-1] if element.text else None


def _first_character(element: etree._Element) -> str | None:
    """The first character within the inline ``element``; None if it has none or starts with a boundary."""
    if element.text:
        return element.text[0]
    for child in element:
        if not _inline(child):
            return None
        first = _first_character(child)
        if first is not None:
            return first
        if child.tail:
            return child.tail[0]
    return None


def _unwrap(content: etree._Element) -> None:
    """Replace ``content`` by its text, joined to the text around it."""
    parent = content.getparent()
    assert parent is not None
    text = (content.text or "") + (content.tail or "")
    previous = content.getprevious()
    if previous is not None:
        previous.tail = (previous.tail or "") + text
    else:
        parent.text = (parent.text or "") + text
    parent.remove(content)


def _in_content(element: etree._Element) -> bool:
    return any(local_name(e) == "content" for e in (element, *element.iterancestors()))
