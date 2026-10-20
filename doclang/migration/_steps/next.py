"""Steps from the development head to the newest released spec version (internal).

Every addition to the head schema that the previous version cannot express adds its rule here.
At release, ``utils/prepare_release.py`` renames this module to ``v<new>_to_<previous>.py`` and
creates a fresh, empty one. Do not mention version numbers in the messages for that reason.
"""

from __future__ import annotations

from lxml import etree

from doclang.migration._tree import Changes


def migrate(root: etree._Element, changes: Changes) -> None:
    """No rules yet."""
