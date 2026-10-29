"""Steps from the newest released spec version to the development head (internal).

Every change in the head that gives existing documents a different meaning adds its rule here, rewriting the
document so that it keeps the meaning it had. At release, ``utils/prepare_release.py`` renames this module to
``v<previous>_to_<new>.py`` and creates a fresh, empty one. Do not mention version numbers in the messages for
that reason.
"""

from __future__ import annotations

from lxml import etree

from doclang.migration._tree import Changes


def migrate(root: etree._Element, changes: Changes) -> None:
    """No rules yet."""
