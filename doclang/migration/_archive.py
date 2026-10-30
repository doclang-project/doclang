"""Bookkeeping of archive members for what a migration removed from the document (internal).

The steps only change the document; the archive members that belong to removed elements are dealt with here:
whole-track media (``audio/{N}.*``, ``video/{N}.*``, aligned with the N-th ``<track>``) and assets referenced
(via ``<src uri>``) only by removed elements. Such members are kept (and reported as orphaned), except that the
media of the remaining tracks is renumbered to stay aligned with them, and that of removed tracks is removed if
tracks remain (it would pair with another track).
"""

from __future__ import annotations

import posixpath
import re
from collections.abc import Iterable
from urllib.parse import unquote, urlsplit

from lxml import etree

from doclang.migration._tree import Changes, is_element, local_name

_TRACK_MEDIA_RE = re.compile(r"^(audio|video)/([1-9][0-9]*)(\.[^/]+)$")


def tracks(root: etree._Element) -> list[etree._Element]:
    """The ``<track>`` elements in document order, nested ones included (as Annex B counts them)."""
    return [e for e in root.iter() if is_element(e) and local_name(e) == "track"]


def asset_references(root: etree._Element) -> set[str]:
    """The ``assets/`` members referenced by ``<src uri>`` (URIs resolve from the archive root)."""
    references = set()
    for element in root.iter():
        if not is_element(element) or local_name(element) != "src" or element.get("uri") is None:
            continue
        uri = urlsplit(element.get("uri", ""))
        if uri.scheme or uri.netloc:
            continue
        path = posixpath.normpath(unquote(uri.path)).lstrip("/")
        if path.startswith("assets/"):
            references.add(path)
    return references


def member_renames(
    names: Iterable[str],
    tracks_before: list[etree._Element],
    assets_before: set[str],
    root: etree._Element,
    changes: Changes,
) -> dict[str, str | None]:
    """The members to rename (to their new name) or remove (to None) after the migration of ``root``.

    ``tracks_before`` and ``assets_before`` are the tracks and asset references before the migration (a track
    is recognized as kept by identity). Whole-track media of the kept tracks is renumbered; that of removed
    tracks is removed if any tracks remain, otherwise it is kept and reported as orphaned, like the assets
    referenced only by removed elements. Media numbered beyond the original tracks and other members are left
    alone.
    """
    positions = {id(track): n for n, track in enumerate(tracks(root), start=1)}
    new_positions = [positions.get(id(track)) for track in tracks_before]
    referenced = asset_references(root)
    renames: dict[str, str | None] = {}
    for name in names:
        match = _TRACK_MEDIA_RE.match(name)
        if match and int(match[2]) <= len(tracks_before):
            new = new_positions[int(match[2]) - 1]
            if new is None and positions:
                renames[name] = None
                changes.record_member("removed", name, f"whole-track media of the removed <track> {match[2]}")
            elif new is None:
                changes.record_member("orphaned", name, f"kept, but its <track> {match[2]} was removed")
            elif new != int(match[2]):
                renames[name] = f"{match[1]}/{new}{match[3]}"
                changes.record_member(
                    "renamed",
                    name,
                    f"renamed to {renames[name]}, as <track> {match[2]} is now <track> {new}",
                )
        elif name in assets_before and name not in referenced:
            changes.record_member("orphaned", name, "kept, but only removed elements referenced it")
    return renames
