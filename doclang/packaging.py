"""Public packaging API for DocLang archives."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Union

from doclang._packaging import PackagingError, _pack

__all__ = ["PackagingError", "pack"]


def pack(
    document: Union[str, Path],
    *,
    output: Union[str, Path, None] = None,
    pages: (Union[str, Path] | Sequence[Union[str, Path]] | Mapping[int, Union[str, Path]] | None) = None,
    assets: (Union[str, Path] | Mapping[str, Union[str, Path]] | None) = None,
    audio: (Union[str, Path] | Sequence[Union[str, Path]] | Mapping[int, Union[str, Path]] | None) = None,
    video: (Union[str, Path] | Sequence[Union[str, Path]] | Mapping[int, Union[str, Path]] | None) = None,
    source: Union[str, Path, bytes, None] = None,
    source_mimetype: str | None = None,
    source_name: str | None = None,
    validate: bool = False,
) -> Path:
    """Pack a DocLang markup file and optional media into a ``.dclx`` OPC archive.

    ``document`` is copied to ``document.xml`` inside the archive. OPC metadata
    (``[Content_Types].xml``, ``_rels/.rels``) is generated automatically.

    By default, writes ``<document>.dclx`` next to the input file. Pass ``output``
    to choose a different path.

    ``pages`` may be a directory (copied into ``pages/``), a sequence of image
    paths (renumbered as ``1.ext``, ``2.ext``, …), or a mapping of page number
    to image path.

    ``audio`` and ``video`` carry whole-track media, one file per ``<track>``,
    placed under ``audio/`` and ``video/`` as ``{N}.{ext}`` where ``N`` is the
    1-based position of the ``<track>`` in document order. Each accepts the same
    forms as ``pages`` (directory, sequence, or ``{track_number: path}`` mapping);
    the mapping form suits the common sparse case where only some tracks have media.

    ``assets`` may be a directory (copied into ``assets/``) or a mapping of
    archive-relative asset path to source file.

    ``source`` is the original document (from which the markup was produced) as
    raw bytes or a file path. The archive stores the bytes unchanged in the part
    ``source.<ext>``, with the extension(s) of the original file name (up to
    two, e.g. ``source.tar.gz``) (``source_name``
    if given, else the file's own name), or in ``source`` without a reliable one,
    and locates it with a package relationship in ``_rels/.rels``. A source file
    that is also packed otherwise (e.g. as ``audio`` when converting a single
    recording) is not stored twice: the relationship targets that part.

    ``source_mimetype`` is the original's MIME type. It is needed when the part's
    extension has no content type yet (always for bytes without ``source_name``),
    and is recorded in ``[Content_Types].xml``.

    ``source_name`` is the original file name. When given, it is recorded in a
    source descriptor part (``source-metadata.xml``); otherwise the original name is not
    kept, as the part's name is only a storage name.

    Symbolic links are refused for ``pages``, ``audio``, ``video``, ``assets``
    and a source file (including entries inside directories) so pack does not
    follow link targets into the archive.

    Returns the resolved path to the created archive.

    Raises :class:`PackagingError` on packaging failure (including symbolic links).
    Raises :class:`~doclang.ValidationError` when ``validate=True`` and the
    archive fails validation (its document or the archive rules of Annex B).
    """
    return _pack(
        document,
        output=output,
        pages=pages,
        assets=assets,
        audio=audio,
        video=video,
        source=source,
        source_mimetype=source_mimetype,
        source_name=source_name,
        validate=validate,
    )
