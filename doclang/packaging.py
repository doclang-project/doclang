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

    ``assets`` may be a directory (copied into ``assets/``) or a mapping of
    archive-relative asset path to source file.

    Symbolic links are refused for ``pages`` and ``assets`` (including entries
    inside directories) so pack does not follow link targets into the archive.

    Returns the resolved path to the created archive.

    Raises :class:`PackagingError` on packaging failure (including symbolic links).
    Raises :class:`~doclang.ValidationError` when ``validate=True`` and the
    document fails validation.
    """
    return _pack(
        document,
        output=output,
        pages=pages,
        assets=assets,
        validate=validate,
    )
