"""Steps from spec version 0.9 to 0.8 (internal)."""

from __future__ import annotations

import re

from lxml import etree

from doclang.migration._tree import Changes, is_element, local_name, remove_keeping_tail

_WHITESPACE = " \t\r\n"
# The source's terms, as of this step (kept here, so that the step does not change with later versions):
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
_PIECES = re.compile(r"[ \t\r\n]+|[^ \t\r\n]+")
_FORMATTING = frozenset("bold italic underline strikethrough superscript subscript handwriting rtl".split())


def migrate(root: etree._Element, changes: Changes) -> None:
    _move_content_out_of_field_headings(root, changes)
    _reduce_markers(root, changes)
    _keep_spaces(root, changes)


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


def _reduce_markers(root: etree._Element, changes: Changes) -> None:
    """A <marker> can hold any semantic elements now, like a <text>; in the target, it holds its element head and
    text-level content only. A <text> or <hint> with text-level content only, or a <marker> without an element head,
    is unwrapped (a <marker> after reducing its own content); other elements (e.g. a <picture> or a <formula>) are
    dropped."""
    unwrapped: list[etree._Element] = []
    dropped: list[etree._Element] = []

    def reduce(marker: etree._Element) -> None:
        for element in [c for c in marker if is_element(c)]:
            name = local_name(element)
            if name in _TEXT_LEVEL or name in _HEAD:
                continue
            if (
                name in ("text", "hint")
                and all(local_name(d) in _TEXT_LEVEL for d in element.iterdescendants() if is_element(d))
            ) or (name == "marker" and not any(is_element(c) and local_name(c) in _HEAD for c in element)):
                changes.record("mapped", element, f"<{name}> in a <marker> unwrapped into the marker's text")
                unwrapped.append(element)
                if name == "marker":
                    reduce(element)
            else:
                changes.record("dropped", element, f"<{name}> in a <marker> has no equivalent in the target version")
                dropped.append(element)

    for marker in [e for e in root.iter() if is_element(e) and local_name(e) == "marker"]:
        if not any(local_name(a) == "marker" for a in marker.iterancestors()):
            reduce(marker)
    for element in dropped:  # recorded first, in document order: changing the tree shifts the positions
        remove_keeping_tail(element)
    for element in reversed(unwrapped):  # inner ones first
        _unwrap(element)


def _unwrap(element: etree._Element) -> None:
    """Replace ``element`` by its content."""
    parent = element.getparent()
    assert parent is not None
    previous = element.getprevious()
    text = element.text or ""
    if previous is not None:
        previous.tail = (previous.tail or "") + text or None
    else:
        parent.text = (parent.text or "") + text or None
    position = parent.index(element)
    children = list(element)
    if children:
        children[-1].tail = (children[-1].tail or "") + (element.tail or "") or None
    elif previous is not None:
        previous.tail = (previous.tail or "") + (element.tail or "") or None
    else:
        parent.text = (parent.text or "") + (element.tail or "") or None
    parent.remove(element)
    for offset, child in enumerate(children):
        parent.insert(position + offset, child)


def _formatting(element: etree._Element | None) -> bool:
    return element is not None and is_element(element) and local_name(element) in _FORMATTING


def _keep_spaces(root: etree._Element, changes: Changes) -> None:
    """Whitespace outside <content> reads as a single space now, also across inline tags; in the target, only
    <content> is guaranteed to keep whitespace: every other text is stripped, and the pieces are joined directly. So
    each space that would get lost, i.e. whitespace that reads as a space and only lies at the start or end of texts,
    becomes a <content> space, where its first character is (so that it keeps its formatting). Whitespace with a line
    break stays, to keep the layout (the target ignores it); other whitespace of the space is removed. Whitespace
    between words stays as it is, as before.

    <field_heading> cannot hold <content>: there, the space goes into the formatting element next to it.
    """
    pieces = []  # (node, "text" or "tail", start, end, whether it holds the first character of a lost space)
    for element in root.iter():
        if is_element(element) and _block_level(element) and not _in_content(element):
            for run in _runs(element):
                pieces += _lost_spaces(run)
    namespace = etree.QName(root).namespace
    moved = []
    for node, attribute, start, end, first in sorted(pieces, key=lambda p: -p[2]):  # later ones first, within a text
        text = getattr(node, attribute)
        kept = text[start:end] if "\n" in text[start:end] else ""
        host = node if attribute == "text" else node.getparent()
        if not first or local_name(host) == "field_heading":
            setattr(node, attribute, text[:start] + kept + text[end:] or None)
            if first:
                moved.append((node, attribute, start == 0))
            continue
        space = etree.Element(f"{{{namespace}}}content" if namespace else "content")
        space.text, space.tail = " ", kept + text[end:] or None
        setattr(node, attribute, text[:start] or None)
        if attribute == "text":
            node.insert(0, space)
        else:
            node.addnext(space)
    for node, attribute, at_start in moved:  # after the others, which change the texts of the formatting elements
        space = etree.Element(f"{{{namespace}}}content" if namespace else "content")
        space.text = " "
        following = node[0] if attribute == "text" else node.getnext()
        if attribute == "tail" and at_start and _inline(node):  # at the end of the formatting element before
            node.append(space)
        elif following is not None and _inline(following):  # at the start of the one after
            space.tail, following.text = following.text, None
            following.insert(0, space)
        else:  # e.g. next to a <checkbox/>
            changes.record(
                "dropped",
                node if attribute == "text" else node.getparent(),
                "space lost, as <field_heading> cannot hold <content> and there is no formatting element next to it",
            )
            continue
        changes.record(
            "mapped",
            space.getparent().getparent(),
            "space kept in a formatting element, as <field_heading> cannot hold <content>",
        )


def _runs(element: etree._Element) -> list[list[tuple]]:
    """The runs of inline content in ``element``'s body, each a list of items: ("ws" or "word", node, attribute,
    start, end) for the pieces of texts, ("tag",) for the tags of inline elements, ("literal",) for <content> and
    for elements without raw text, e.g. a <checkbox/>, which are part of the text."""
    runs: list[list[tuple]] = [[]]

    def add(node: etree._Element, attribute: str) -> None:
        text = getattr(node, attribute) or ""
        for piece in _PIECES.finditer(text):
            kind = "ws" if piece.group()[0] in _WHITESPACE else "word"
            runs[-1].append((kind, node, attribute, piece.start(), piece.end()))

    def walk(parent: etree._Element) -> None:
        add(parent, "text")
        for child in parent:
            if _inline(child) and local_name(child) == "content":
                runs[-1].append(("literal",))
            elif _inline(child):
                runs[-1].append(("tag",))
                walk(child)
                runs[-1].append(("tag",))
            elif not is_element(child) or local_name(child) in _HEAD:
                pass  # disregarded: a comment, a processing instruction, an element head (e.g. a caption is a
                # text block of its own)
            elif is_element(child) and local_name(child) in _SEMANTIC:
                runs.append([])  # e.g. one of two <text> paragraphs in a list item: a block of its own
            elif is_element(child) and local_name(child) not in _DELIMITERS:
                runs[-1].append(("literal",))
            else:
                runs.append([])  # a delimiter
            add(child, "tail")

    walk(element)
    return runs


def _lost_spaces(run: list[tuple]) -> list[tuple]:
    """The whitespace pieces in ``run`` of each space that the target would lose: a sequence of whitespace that
    reads as a space and has no word on both sides within the same text. The first piece holds its first
    character."""
    content = [i for i, item in enumerate(run) if item[0] in ("word", "literal")]
    lost = []
    i = content[0] + 1 if content else len(run)
    while i < (content[-1] if content else 0):
        if run[i][0] != "ws":
            i += 1
            continue
        sequence = [i]
        while run[sequence[-1] + 1][0] in ("ws", "tag"):
            sequence.append(sequence[-1] + 1)
        if not any(_between_words(run, j) for j in sequence):
            lost += [(*run[j][1:], j == i) for j in sequence if run[j][0] == "ws"]
        i = sequence[-1] + 1
    return lost


def _between_words(run: list[tuple], i: int) -> bool:
    """Whether ``run[i]`` is whitespace with a word on both sides within the same text (the target keeps it)."""
    return run[i][0] == "ws" and all(n[0] == "word" and n[1:3] == run[i][1:3] for n in (run[i - 1], run[i + 1]))


def _block_level(element: etree._Element) -> bool:
    name = local_name(element)
    return (name in _RAW_TEXT or name in _VIRTUAL_TEXT) and not _inline(element)


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


def _in_content(element: etree._Element) -> bool:
    return any(local_name(e) == "content" for e in (element, *element.iterancestors()))
