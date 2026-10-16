"""Steps from the development head to the newest released spec version (internal).

Every addition to the head schema that the previous version cannot express adds its rule here.
At release, ``utils/prepare_release.py`` renames this module to ``v<new>_to_<previous>.py`` and
creates a fresh, empty one. Do not mention version numbers in the messages for that reason.
"""

from __future__ import annotations

from lxml import etree

from doclang.migration._tree import Changes, is_element, local_name, remove_keeping_tail


def migrate(root: etree._Element, changes: Changes) -> None:
    _drop_writing_modes(root, changes)


def _drop_writing_modes(root: etree._Element, changes: Changes) -> None:
    """<writing_mode> has no equivalent in the previous version; the content stays in reading order."""
    for element in list(root.iter()):
        if not is_element(element) or local_name(element) != "writing_mode":
            continue
        changes.record("dropped", element, "<writing_mode> has no equivalent in the target version and was removed")
        remove_keeping_tail(element)
