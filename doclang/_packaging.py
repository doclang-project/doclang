"""Internal implementation for DocLang archive packaging."""

from __future__ import annotations

import copy
import os
import shutil
import tempfile
import time
import zipfile
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Union

_CONTENT_TYPES_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="jpg" ContentType="image/jpeg"/>
  <Default Extension="jpeg" ContentType="image/jpeg"/>
  <Default Extension="webp" ContentType="image/webp"/>
  <Default Extension="mp3" ContentType="audio/mpeg"/>
  <Default Extension="m4a" ContentType="audio/mp4"/>
  <Default Extension="aac" ContentType="audio/aac"/>
  <Default Extension="ogg" ContentType="audio/ogg"/>
  <Default Extension="opus" ContentType="audio/ogg"/>
  <Default Extension="wav" ContentType="audio/wav"/>
  <Default Extension="flac" ContentType="audio/flac"/>
  <Default Extension="mp4" ContentType="video/mp4"/>
  <Default Extension="webm" ContentType="video/webm"/>
  <Default Extension="mkv" ContentType="video/x-matroska"/>
  <Default Extension="mov" ContentType="video/quicktime"/>
  <Override PartName="/document.xml" ContentType="application/vnd.doclang.document+xml"/>
</Types>
"""

_RELS_XML = """\
<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1"
    Type="http://doclang.ai/ns/package/2026/relationships/document"
    Target="document.xml"/>
</Relationships>
"""

PagesInput = Union[
    str,
    Path,
    Sequence[Union[str, Path]],
    Mapping[int, Union[str, Path]],
]

# Whole-track media (audio/, video/) uses the same 1-based positional model as pages/.
MediaInput = PagesInput

AssetsInput = Union[
    str,
    Path,
    Mapping[str, Union[str, Path]],
]


class PackagingError(Exception):
    """Raised when DocLang archive packaging fails."""


def _require_file(path: Path, *, label: str) -> None:
    if not path.is_file():
        raise PackagingError(f"{label} not found or not a file: {path}")


def _require_directory(path: Path, *, label: str) -> None:
    if not path.is_dir():
        raise PackagingError(f"{label} not found or not a directory: {path}")


def _reject_symlink(path: Path, *, label: str) -> None:
    if path.is_symlink():
        raise PackagingError(f"{label} must not be a symbolic link: {path}")


def _validate_archive_relative_path(path: str, *, label: str) -> None:
    if not path or path.startswith("/") or "\\" in path:
        raise PackagingError(f"Invalid {label} path: {path!r}")
    parts = Path(path).parts
    if ".." in parts or path in {".", ".."}:
        raise PackagingError(f"Invalid {label} path: {path!r}")


def _copy_file(source: Path, destination: Path, *, label: str) -> None:
    _reject_symlink(source, label=label)
    _require_file(source, label=label)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _copy_tree_into(source: Path, destination: Path, *, label: str) -> None:
    _reject_symlink(source, label=label)
    _require_directory(source, label=label)
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        _reject_symlink(item, label=label)
        if item.is_dir():
            _copy_tree_into(item, target, label=label)
        else:
            shutil.copy2(item, target)


def _place_document(stage: Path, document: Path) -> None:
    _require_file(document, label="Document")
    shutil.copy2(document, stage / "document.xml")


def _place_indexed(
    stage: Path,
    spec: PagesInput,
    *,
    subdir: str,
    file_label: str,
    dir_label: str,
    number_label: str,
) -> None:
    """Place 1-based positionally-indexed files (``{N}.{ext}``) under ``stage/subdir``.

    Shared by ``pages/`` (page images) and ``audio/`` / ``video/`` (whole-track media),
    which all key a file to an integer position in the document.
    """
    target_dir = stage / subdir
    if isinstance(spec, Mapping):
        for number, source in spec.items():
            if not isinstance(number, int) or number < 1:
                raise PackagingError(f"{number_label} must be positive integers, got {number!r}")
            source_path = Path(source)
            destination = target_dir / f"{number}{source_path.suffix}"
            _copy_file(source_path, destination, label=file_label)
        return

    if isinstance(spec, str | Path):
        _copy_tree_into(Path(spec), target_dir, label=dir_label)
        return

    for index, source in enumerate(spec, start=1):
        source_path = Path(source)
        destination = target_dir / f"{index}{source_path.suffix}"
        _copy_file(source_path, destination, label=file_label)


def _place_pages(stage: Path, pages: PagesInput) -> None:
    _place_indexed(
        stage,
        pages,
        subdir="pages",
        file_label="Page file",
        dir_label="Pages directory",
        number_label="Page numbers",
    )


def _place_audio(stage: Path, audio: MediaInput) -> None:
    _place_indexed(
        stage,
        audio,
        subdir="audio",
        file_label="Audio file",
        dir_label="Audio directory",
        number_label="Audio track numbers",
    )


def _place_video(stage: Path, video: MediaInput) -> None:
    _place_indexed(
        stage,
        video,
        subdir="video",
        file_label="Video file",
        dir_label="Video directory",
        number_label="Video track numbers",
    )


def _place_assets(stage: Path, assets: AssetsInput) -> None:
    assets_dir = stage / "assets"
    if isinstance(assets, Mapping):
        for archive_path, source in assets.items():
            _validate_archive_relative_path(archive_path, label="asset")
            destination = assets_dir / archive_path
            _copy_file(Path(source), destination, label="Asset file")
        return

    _copy_tree_into(Path(assets), assets_dir, label="Assets directory")


def _write_opc_metadata(stage: Path) -> None:
    (stage / "[Content_Types].xml").write_text(_CONTENT_TYPES_XML, encoding="utf-8")
    rels_dir = stage / "_rels"
    rels_dir.mkdir(parents=True, exist_ok=True)
    (rels_dir / ".rels").write_text(_RELS_XML, encoding="utf-8")


def _should_exclude_zip_member(arcname: str) -> bool:
    parts = arcname.split("/")
    if "__MACOSX" in parts:
        return True
    name = parts[-1]
    return name == ".DS_Store" or name.startswith("._")


def _create_zip(stage: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    if output.exists():
        output.unlink()
    with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(stage.rglob("*")):
            if not path.is_file():
                continue
            arcname = path.relative_to(stage).as_posix()
            if _should_exclude_zip_member(arcname):
                continue
            archive.write(path, arcname)


def _pack(
    document: Union[str, Path],
    *,
    output: Union[str, Path, None] = None,
    pages: PagesInput | None = None,
    assets: AssetsInput | None = None,
    audio: MediaInput | None = None,
    video: MediaInput | None = None,
    validate: bool = False,
) -> Path:
    document_path = Path(document)
    output_path = Path(output) if output is not None else document_path.with_suffix(".dclx")

    with tempfile.TemporaryDirectory() as temp_dir:
        stage = Path(temp_dir)
        _place_document(stage, document_path)
        if pages is not None:
            _place_pages(stage, pages)
        if assets is not None:
            _place_assets(stage, assets)
        if audio is not None:
            _place_audio(stage, audio)
        if video is not None:
            _place_video(stage, video)
        _write_opc_metadata(stage)

        if validate:
            from doclang.validation import validate as validate_document

            validate_document(stage / "document.xml")

        _create_zip(stage, output_path)

    return output_path.resolve()


def _is_archive(path: Union[str, Path]) -> bool:
    """Whether ``path`` is a DocLang archive (a ZIP file) rather than bare markup."""
    return Path(path).is_file() and zipfile.is_zipfile(path)


def _read_archive(path: Union[str, Path]) -> tuple[list[zipfile.ZipInfo], bytes]:
    """The members of the archive ``path`` and the content of its ``document.xml``.

    Refuses archives with unsafe or duplicate member names, encrypted members or no ``document.xml``.
    """
    try:
        with zipfile.ZipFile(path) as archive:
            members = archive.infolist()
            names = [member.filename for member in members]
            for member in members:
                _validate_archive_relative_path(member.filename, label="archive member")
                if member.flag_bits & 0x1:
                    raise PackagingError(f"Encrypted archive member: {member.filename!r}")
            if len(set(names)) != len(names):
                raise PackagingError(f"Duplicate archive members in {path}")
            if "document.xml" not in names:
                raise PackagingError(f"No document.xml in archive {path}")
            return members, archive.read("document.xml")
    except zipfile.BadZipFile as exc:
        raise PackagingError(f"Invalid archive {path}: {exc}") from exc


@contextmanager
def _document_file(path: Union[str, Path]) -> Iterator[Path]:
    """The markup file of ``path``: ``path`` itself, or a temporary copy of an archive's ``document.xml``."""
    if not _is_archive(path):
        yield Path(path)
        return
    _, document = _read_archive(path)
    with tempfile.TemporaryDirectory() as temp_dir:
        extracted = Path(temp_dir) / "document.xml"
        extracted.write_bytes(document)
        yield extracted


def _write_archive(
    source: Union[str, Path],
    output: Union[str, Path],
    document: bytes,
    renames: Mapping[str, str | None],
) -> None:
    """Write a copy of the archive ``source`` to ``output`` with ``document`` as its ``document.xml``.

    ``renames`` maps member names to new names, or to None to leave the member out. Every other member is
    copied as is, with its zip metadata, in the original order. ``output`` may be ``source``.
    """
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=output_path.parent, suffix=".dclx", delete=False) as temp:
        temp_path = Path(temp.name)
    try:
        with zipfile.ZipFile(source) as archive_in, zipfile.ZipFile(temp_path, "w") as archive_out:
            archive_out.comment = archive_in.comment
            for member in archive_in.infolist():
                name = renames.get(member.filename, member.filename)
                if name is None:
                    continue
                info = copy.copy(member)
                info.filename = name
                if member.filename == "document.xml":
                    info.date_time = time.localtime()[:6]
                    archive_out.writestr(info, document)
                elif member.is_dir():
                    archive_out.writestr(info, b"")
                else:  # streamed: media can be large
                    with archive_in.open(member) as data, archive_out.open(info, "w") as copied:
                        shutil.copyfileobj(data, copied)
        os.replace(temp_path, output_path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise
