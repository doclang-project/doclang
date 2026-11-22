"""Bookkeeping of archive members for what a migration removed from the document (internal).

The steps only change the document; the archive members that belong to removed elements are dealt with here:
whole-track media (``audio/{N}.*``, ``video/{N}.*``, aligned with the N-th ``<track>``) and assets referenced
(via ``<src uri>``) only by removed elements. Such members are kept (and reported as orphaned), except that the
media of the remaining tracks is renumbered to stay aligned with them, and that of removed tracks is removed if
tracks remain (it would pair with another track), unless a package relationship targets it (e.g. as the archive's
original source): then it is moved out of the way to ``source.<ext>``.
"""

from __future__ import annotations

from collections.abc import Collection, Iterable

from lxml import etree

from doclang._packaging import _TRACK_MEDIA_RE, _markup_references
from doclang._packaging import _tracks as tracks
from doclang.migration._tree import Changes


def asset_references(root: etree._Element) -> set[str]:
    """The ``assets/`` members referenced by ``<src uri>`` (URIs resolve from the archive root)."""
    return {part for part in _markup_references(root)[0] if part.startswith("assets/")}


def member_renames(
    names: Iterable[str],
    tracks_before: list[etree._Element],
    assets_before: set[str],
    root: etree._Element,
    changes: Changes,
    targets: Collection[str] = (),
) -> dict[str, str | None]:
    """The members to rename (to their new name) or remove (to None) after the migration of ``root``.

    ``tracks_before`` and ``assets_before`` are the tracks and asset references before the migration (a track
    is recognized as kept by identity). Whole-track media of the kept tracks is renumbered; that of removed
    tracks is removed if any tracks remain, otherwise it is kept and reported as orphaned, like the assets
    referenced only by removed elements. Media of removed tracks that is the target of a package relationship
    (one of ``targets``) is moved to ``source.<ext>`` instead of being removed. Media numbered beyond the original
    tracks and other members are left alone.
    """
    positions = {id(track): n for n, track in enumerate(tracks(root), start=1)}
    new_positions = [positions.get(id(track)) for track in tracks_before]
    referenced = asset_references(root)
    renames: dict[str, str | None] = {}
    for name in names:
        match = _TRACK_MEDIA_RE.fullmatch(name)
        if match and int(match[2]) <= len(tracks_before):
            new = new_positions[int(match[2]) - 1]
            if new is None and positions and name in targets:
                renames[name] = _free_name(f"source{match[3]}", set(names) | set(renames.values()))
                changes.record_member(
                    "renamed",
                    name,
                    f"renamed to {renames[name]}: a package relationship targets this whole-track media of the "
                    f"removed <track> {match[2]}, which would otherwise pair with another track",
                )
            elif new is None and positions:
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


def _free_name(name: str, taken: Collection[str | None]) -> str:
    """``name``, or ``name`` with a number before its extension, whichever is not ``taken``."""
    stem, dot, extension = name.partition(".")
    number = 1
    while name in taken:
        number += 1
        name = f"{stem}-{number}{dot}{extension}"
    return name
