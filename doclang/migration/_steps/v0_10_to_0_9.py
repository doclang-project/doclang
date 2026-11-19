"""Steps from spec version 0.10 to 0.9 (internal)."""

from __future__ import annotations

from lxml import etree

from doclang.migration._tree import Changes


def migrate(root: etree._Element, changes: Changes) -> None:
    """No rules yet."""
