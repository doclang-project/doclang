"""Internal implementation for DocLang archive packaging."""

from __future__ import annotations

import copy
import os
import posixpath
import re
import shutil
import tempfile
import time
import zipfile
from collections.abc import Callable, Iterator, Mapping, Sequence
from contextlib import contextmanager
from pathlib import Path
from typing import Union
from urllib.parse import unquote, urlsplit
from xml.sax.saxutils import quoteattr

from lxml import etree

from doclang._schemas import _VERSION_RE, _declared_version, _version_key

_CONTENT_TYPES_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/content-types"
_RELATIONSHIPS_NAMESPACE = "http://schemas.openxmlformats.org/package/2006/relationships"

_RELATIONSHIP_TYPES = "http://doclang.ai/ns/package/2026/relationships/"
_DOCUMENT_RELATIONSHIP = _RELATIONSHIP_TYPES + "document"
_SOURCE_RELATIONSHIP = _RELATIONSHIP_TYPES + "source"
_SOURCE_METADATA_RELATIONSHIP = _RELATIONSHIP_TYPES + "source-metadata"

_SOURCE_METADATA_NAMESPACE = "http://doclang.ai/ns/package/2026/source-metadata"
_SOURCE_METADATA_CONTENT_TYPE = "application/vnd.doclang.source-metadata+xml"

_DEFAULT_CONTENT_TYPES = {
    "rels": "application/vnd.openxmlformats-package.relationships+xml",
    "png": "image/png",
    "jpg": "image/jpeg",
    "jpeg": "image/jpeg",
    "webp": "image/webp",
    "svg": "image/svg+xml",
    "mp3": "audio/mpeg",
    "m4a": "audio/mp4",
    "aac": "audio/aac",
    "ogg": "audio/ogg",
    "opus": "audio/ogg",
    "wav": "audio/wav",
    "flac": "audio/flac",
    "wma": "audio/x-ms-wma",
    "aif": "audio/x-aiff",
    "aiff": "audio/x-aiff",
    "mp4": "video/mp4",
    "webm": "video/webm",
    "mkv": "video/x-matroska",
    "mov": "video/quicktime",
    "m4v": "video/x-m4v",
    "wmv": "video/x-ms-wmv",
    "asf": "video/x-ms-asf",
    "avi": "video/x-msvideo",
    "mpg": "video/mpeg",
    "mpeg": "video/mpeg",
    "flv": "video/x-flv",
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "doc": "application/msword",
    "xls": "application/vnd.ms-excel",
    "ppt": "application/vnd.ms-powerpoint",
}
_DOCUMENT_CONTENT_TYPE = "application/vnd.doclang.document+xml"

# Positional parts: ``pages/{N}.{ext}`` align with the N-th page, ``audio/{N}.{ext}`` and ``video/{N}.{ext}`` with
# the N-th ``<track>``.
_PAGE_RE = re.compile(r"pages/([1-9][0-9]*)(\.[^/]+)")
_TRACK_MEDIA_RE = re.compile(r"(audio|video)/([1-9][0-9]*)(\.[^/]+)")
# Relationship parts: ``_rels/.rels`` (of the package) and ``{folder}/_rels/{name}.rels`` (of the part
# ``{folder}/{name}``).
_RELATIONSHIP_PART_RE = re.compile(r"((?:[^/]+/)*)_rels/([^/]*)\.rels")

# The first spec version with Annex B (the archive format), and the one with its rules on references from the
# markup and on parts not accounted for.
_FIRST_ARCHIVE_VERSION = (0, 8)
_REFERENCES_VERSION = (0, 10)
_SOURCE_VERSION = (0, 10)  # the original source, located by a relationship

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

SourceInput = Union[str, Path, bytes]
_SOURCE_MIMETYPE_PATTERN = re.compile(r"[A-Za-z0-9!#$&^_.+-]+/[A-Za-z0-9!#$&^_.+-]+\Z")
# Extensions taken over from an original file name into the source part's name (``source.<ext>``).
_SOURCE_EXTENSION_PATTERN = re.compile(r"[a-z0-9]{1,16}\Z")


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


Placed = dict[Path, Path]
"""The input files placed in the stage so far: resolved input path → destination."""


def _copy_file(source: Path, destination: Path, *, label: str, placed: Placed) -> None:
    _reject_symlink(source, label=label)
    _require_file(source, label=label)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    placed.setdefault(source.resolve(), destination)


def _copy_tree_into(source: Path, destination: Path, *, label: str, placed: Placed) -> None:
    _reject_symlink(source, label=label)
    _require_directory(source, label=label)
    destination.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        target = destination / item.name
        _reject_symlink(item, label=label)
        if item.is_dir():
            _copy_tree_into(item, target, label=label, placed=placed)
        else:
            shutil.copy2(item, target)
            placed.setdefault(item.resolve(), target)


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
    placed: Placed,
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
            _copy_file(source_path, destination, label=file_label, placed=placed)
        return

    if isinstance(spec, str | Path):
        _copy_tree_into(Path(spec), target_dir, label=dir_label, placed=placed)
        return

    for index, source in enumerate(spec, start=1):
        source_path = Path(source)
        destination = target_dir / f"{index}{source_path.suffix}"
        _copy_file(source_path, destination, label=file_label, placed=placed)


def _place_pages(stage: Path, pages: PagesInput, placed: Placed) -> None:
    _place_indexed(
        stage,
        pages,
        subdir="pages",
        file_label="Page file",
        dir_label="Pages directory",
        number_label="Page numbers",
        placed=placed,
    )


def _place_audio(stage: Path, audio: MediaInput, placed: Placed) -> None:
    _place_indexed(
        stage,
        audio,
        subdir="audio",
        file_label="Audio file",
        dir_label="Audio directory",
        number_label="Audio track numbers",
        placed=placed,
    )


def _place_video(stage: Path, video: MediaInput, placed: Placed) -> None:
    _place_indexed(
        stage,
        video,
        subdir="video",
        file_label="Video file",
        dir_label="Video directory",
        number_label="Video track numbers",
        placed=placed,
    )


def _place_assets(stage: Path, assets: AssetsInput, placed: Placed) -> None:
    assets_dir = stage / "assets"
    if isinstance(assets, Mapping):
        for archive_path, source in assets.items():
            _validate_archive_relative_path(archive_path, label="asset")
            destination = assets_dir / archive_path
            _copy_file(Path(source), destination, label="Asset file", placed=placed)
        return

    _copy_tree_into(Path(assets), assets_dir, label="Assets directory", placed=placed)


def _extension(part: str) -> str | None:
    """The extension of the part ``part`` (as OPC matches ``<Default>``), lowercased, or None."""
    name = part.rsplit("/", 1)[-1]
    return name.rsplit(".", 1)[1].lower() if "." in name else None


def _source_part_name(source: SourceInput, name: str | None) -> str:
    """``source.<ext>`` with the extensions of the original file name (up to two, e.g. ``source.tar.gz``), or
    ``source`` without a reliable one."""
    original = name if name is not None else (None if isinstance(source, bytes) else Path(source).name)
    if original is None:
        return "source"
    stem, *extensions = original.lower().split(".")
    if not stem or not extensions or extensions[-1] == "rels":
        return "source"
    kept: list[str] = []
    for extension in reversed(extensions[-2:]):
        if _SOURCE_EXTENSION_PATTERN.fullmatch(extension) is None:
            break
        kept.insert(0, extension)
    return f"source.{'.'.join(kept)}" if kept else "source"


def _check_source_name(name: str) -> None:
    if (
        not name
        or name in {".", ".."}
        or any(c in name for c in "/\\")
        or any(ord(c) < 32 or ord(c) == 127 for c in name)
    ):
        raise PackagingError(f"Invalid source file name: {name!r}")


def _place_source(stage: Path, source: SourceInput, name: str | None, placed: Placed) -> str:
    """Place the original source, unless it is a file already placed (e.g. the whole-track media of a single
    recording); return its part name."""
    if not isinstance(source, bytes):
        _reject_symlink(Path(source), label="Source document")
        destination = placed.get(Path(source).resolve())
        if destination is not None:
            return destination.relative_to(stage).as_posix()
    part = _source_part_name(source, name)
    if isinstance(source, bytes):
        (stage / part).write_bytes(source)
    else:
        _copy_file(Path(source), stage / part, label="Source document", placed=placed)
    return part


def _declare_content_type(
    part: str, content_type: str | None, defaults: dict[str, str], overrides: dict[str, str]
) -> None:
    """Make sure ``part`` has a content type (``content_type`` if given): a ``<Default>`` for its extension if
    there is none yet, else an ``<Override>`` if the existing one differs."""
    extension = _extension(part)
    current = overrides.get(part) or (defaults.get(extension) if extension else None)
    if content_type is None:
        if current is None:
            raise PackagingError(f"No content type known for the source part {part!r}; pass its MIME type")
    elif content_type != current:
        if _SOURCE_MIMETYPE_PATTERN.fullmatch(content_type) is None:
            raise PackagingError("Invalid source MIME type; expected type/subtype")
        if extension is not None and extension not in defaults and part not in overrides:
            defaults[extension] = content_type
        else:
            overrides[part] = content_type


def _source_metadata_xml(name: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f"<source xmlns={quoteattr(_SOURCE_METADATA_NAMESPACE)} name={quoteattr(name)}/>\n"
    )


def _write_opc_metadata(
    stage: Path,
    defaults: Mapping[str, str],
    overrides: Mapping[str, str],
    relationships: Sequence[tuple[str, str]],
) -> None:
    """Write ``_rels/.rels`` and ``[Content_Types].xml``; ``relationships`` are (type, target part) pairs, and of
    ``defaults`` only the extensions of parts without an override are declared."""
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', f'<Relationships xmlns="{_RELATIONSHIPS_NAMESPACE}">']
    for number, (relationship_type, target) in enumerate(relationships, start=1):
        lines += [
            f'  <Relationship Id="rId{number}"',
            f"    Type={quoteattr(relationship_type)}",
            f"    Target={quoteattr(target)}/>",
        ]
    lines.append("</Relationships>")
    rels_dir = stage / "_rels"
    rels_dir.mkdir(parents=True, exist_ok=True)
    (rels_dir / ".rels").write_text("\n".join(lines) + "\n", encoding="utf-8")

    used = {
        _extension(part)
        for part in (path.relative_to(stage).as_posix() for path in stage.rglob("*") if path.is_file())
        if part not in overrides and not _should_exclude_zip_member(part)
    }
    lines = ['<?xml version="1.0" encoding="UTF-8"?>', f'<Types xmlns="{_CONTENT_TYPES_NAMESPACE}">']
    lines += [
        f"  <Default Extension={quoteattr(ext)} ContentType={quoteattr(ct)}/>"
        for ext, ct in defaults.items()
        if ext in used
    ]
    lines += [f"  <Override PartName={quoteattr('/' + p)} ContentType={quoteattr(ct)}/>" for p, ct in overrides.items()]
    lines.append("</Types>")
    (stage / "[Content_Types].xml").write_text("\n".join(lines) + "\n", encoding="utf-8")


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
    source: SourceInput | None = None,
    source_mimetype: str | None = None,
    source_name: str | None = None,
    validate: bool = False,
) -> Path:
    if source is None and (source_mimetype is not None or source_name is not None):
        raise PackagingError("source_mimetype and source_name need source")
    if source_name is not None:
        _check_source_name(source_name)
    document_path = Path(document)
    output_path = Path(output) if output is not None else document_path.with_suffix(".dclx")

    with tempfile.TemporaryDirectory() as temp_dir:
        stage = Path(temp_dir)
        placed: Placed = {}
        _place_document(stage, document_path)
        if pages is not None:
            _place_pages(stage, pages, placed)
        if assets is not None:
            _place_assets(stage, assets, placed)
        if audio is not None:
            _place_audio(stage, audio, placed)
        if video is not None:
            _place_video(stage, video, placed)
        defaults = dict(_DEFAULT_CONTENT_TYPES)
        overrides = {"document.xml": _DOCUMENT_CONTENT_TYPE}
        relationships = [(_DOCUMENT_RELATIONSHIP, "document.xml")]
        if source is not None:
            part = _place_source(stage, source, source_name, placed)
            _declare_content_type(part, source_mimetype, defaults, overrides)
            relationships.append((_SOURCE_RELATIONSHIP, part))
            if source_name is not None:
                descriptor = "source-metadata.xml"
                (stage / descriptor).write_text(_source_metadata_xml(source_name), encoding="utf-8")
                overrides[descriptor] = _SOURCE_METADATA_CONTENT_TYPE
                relationships.append((_SOURCE_METADATA_RELATIONSHIP, descriptor))
        _write_opc_metadata(stage, defaults, overrides, relationships)

        if validate:  # the archive, before it replaces any existing output
            from doclang.validation import validate as validate_document

            with tempfile.TemporaryDirectory() as zip_dir:
                archive = Path(zip_dir) / output_path.name
                _create_zip(stage, archive)
                validate_document(archive)
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(archive, output_path)
        else:
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

    ``renames`` maps member names to new names, or to None to leave the member out; package relationships and
    content type overrides follow. Every other member is copied as is, with its zip metadata, in the original
    order. ``output`` may be ``source``.
    """
    output_path = Path(output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source) as archive_in:
        metadata = _renamed_opc_metadata(archive_in, renames)
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
                elif member.filename in metadata:
                    archive_out.writestr(info, metadata[member.filename])
                elif member.is_dir():
                    archive_out.writestr(info, b"")
                else:  # streamed: media can be large
                    with archive_in.open(member) as data, archive_out.open(info, "w") as copied:
                        shutil.copyfileobj(data, copied)
        os.replace(temp_path, output_path)
    except BaseException:
        temp_path.unlink(missing_ok=True)
        raise


# --- archive rules (Annex B) -------------------------------------------------------------------------


def _archive_rules_version(document: Path, spec_version: str | None) -> tuple[int, int] | None:
    """The spec version whose archive rules apply to the archive of the markup file ``document``:
    ``spec_version`` if given, else the declared one, else None (the latest). A declared version counts even
    without bundled schemas, as the archive rules are not part of the schemas."""
    version = spec_version if spec_version is not None else _declared_version(document)
    return _version_key(version) if version is not None and _VERSION_RE.fullmatch(version) else None


def _archive_rules_apply(version: tuple[int, int] | None, since: tuple[int, int] = _FIRST_ARCHIVE_VERSION) -> bool:
    """Whether archive rules introduced in the spec version ``since`` apply to a document of the spec ``version``
    (None for the latest)."""
    return version is None or version >= since


def _parse_xml(data: bytes) -> etree._Element:
    return etree.fromstring(data, etree.XMLParser(resolve_entities=False, no_network=True))


def _relationship_target_part(target: str, base: str = "") -> str:
    """The part an internal relationship's target refers to: relative to the folder ``base`` (e.g. ``audio/``) of
    the part whose relationships it is, which is the root for package relationships."""
    path = unquote(urlsplit(target).path)
    return posixpath.normpath(path if path.startswith("/") else f"/{base}{path}").lstrip("/")


def _package_relationships(archive: zipfile.ZipFile) -> list[etree._Element] | None:
    """The ``<Relationship>`` elements of ``_rels/.rels``, or None if there is none (raises on bad XML)."""
    if "_rels/.rels" not in archive.namelist():
        return None
    return list(_parse_xml(archive.read("_rels/.rels")).iterfind(f"{{{_RELATIONSHIPS_NAMESPACE}}}Relationship"))


def _content_type_maps(archive: zipfile.ZipFile) -> tuple[dict[str, str], dict[str, str]]:
    """The ``<Default>`` content types by lowercased extension and the ``<Override>`` ones by lowercased part
    name (OPC compares both case-insensitively); empty without ``[Content_Types].xml`` (raises on bad XML)."""
    defaults: dict[str, str] = {}
    overrides: dict[str, str] = {}
    if "[Content_Types].xml" in archive.namelist():
        root = _parse_xml(archive.read("[Content_Types].xml"))
        for element in root.iterfind(f"{{{_CONTENT_TYPES_NAMESPACE}}}Default"):
            defaults[element.get("Extension", "").lower()] = element.get("ContentType", "")
        for element in root.iterfind(f"{{{_CONTENT_TYPES_NAMESPACE}}}Override"):
            overrides[element.get("PartName", "").lstrip("/").lower()] = element.get("ContentType", "")
    return defaults, overrides


def _local_name(node: etree._Element) -> str | None:
    """The local name of an element, or None for comments and processing instructions."""
    return etree.QName(node).localname if isinstance(node.tag, str) else None


def _tracks(root: etree._Element) -> list[etree._Element]:
    """The ``<track>`` elements in document order, nested ones included (as Annex B counts them)."""
    return [e for e in root.iter() if _local_name(e) == "track"]


def _page_count(root: etree._Element) -> int:
    """The number of pages of the document ``root``: its ``<page_break/>`` elements outside ``<head>``, plus one."""
    return 1 + sum(
        1
        for e in root.iter()
        if _local_name(e) == "page_break" and not any(_local_name(a) == "head" for a in e.iterancestors())
    )


def _markup_references(root: etree._Element) -> tuple[set[str], set[str]]:
    """The parts that the relative URIs of the ``<src>`` and of the ``<href>`` elements of the markup ``root``
    refer to (they resolve from the archive root)."""
    sources: set[str] = set()
    links: set[str] = set()
    for element in root.iter():
        name = _local_name(element)
        if name not in ("src", "href") or element.get("uri") is None:
            continue
        uri = urlsplit(element.get("uri", ""))
        part = posixpath.normpath("/" + unquote(uri.path)).lstrip("/")
        if not uri.scheme and not uri.netloc and part:
            (sources if name == "src" else links).add(part)
    return sources, links


def _relationship_targets_of_parts(archive: zipfile.ZipFile, parts: list[str]) -> set[str]:
    """The parts targeted by the internal relationships of the package and of its parts (relationship parts that
    are not well-formed are skipped)."""
    targets = set()
    for name in parts:
        match = _RELATIONSHIP_PART_RE.fullmatch(name)
        if match is None:
            continue
        try:
            root = _parse_xml(archive.read(name))
        except etree.XMLSyntaxError:
            continue
        for relationship in root.iterfind(f"{{{_RELATIONSHIPS_NAMESPACE}}}Relationship"):
            if relationship.get("TargetMode") != "External":
                targets.add(_relationship_target_part(relationship.get("Target", ""), match[1]))
    return targets


Problems = list[dict[str, str]]
"""Archive rule violations, each with the ``location`` (a part name) and a ``message``."""


def _check_archive(path: Union[str, Path], version: tuple[int, int] | None) -> tuple[Problems, Problems]:
    """The errors and warnings on the rules of Annex B for a document of the spec ``version`` (None for the
    latest) in the archive ``path``, apart from the validity of its ``document.xml``: the OPC metadata
    (``[Content_Types].xml``, ``_rels/.rels``), the original source and its descriptor, the positional parts
    (``pages/``, ``audio/``, ``video/``), and
    the parts referenced from the markup or not accounted for. The archive must be readable (see
    ``_read_archive``).
    """
    errors: Problems = []
    warnings: Problems = []

    def error(location: str, message: str) -> None:
        errors.append({"location": location, "message": message})

    def warning(location: str, message: str) -> None:
        warnings.append({"location": location, "message": message})

    with zipfile.ZipFile(path) as archive:
        parts = [name for name in archive.namelist() if not name.endswith("/")]
        _check_content_types(archive, parts, error)
        _check_package_relationships(archive, error)
        if _archive_rules_apply(version, _SOURCE_VERSION):
            _check_source(archive, parts, error)
        try:
            root = _parse_xml(archive.read("document.xml"))
        except etree.XMLSyntaxError:
            return errors, warnings  # reported by the validation of document.xml
        _check_positional_parts(root, parts, error)
        if _archive_rules_apply(version, _REFERENCES_VERSION):
            _check_references(root, parts, _relationship_targets_of_parts(archive, parts), error, warning)
    return errors, warnings


def _check_content_types(archive: zipfile.ZipFile, parts: list[str], error: Callable[[str, str], None]) -> None:
    if "[Content_Types].xml" not in parts:
        error("[Content_Types].xml", "Missing")
        return
    try:
        defaults, overrides = _content_type_maps(archive)
    except etree.XMLSyntaxError as exc:
        error("[Content_Types].xml", f"Not well-formed XML: {exc}")
        return
    if overrides.get("document.xml") != _DOCUMENT_CONTENT_TYPE:
        error("[Content_Types].xml", f"No <Override> for /document.xml with the content type {_DOCUMENT_CONTENT_TYPE}")
    for part in parts:
        extension = _extension(part)
        if part != "[Content_Types].xml" and part.lower() not in overrides and extension not in defaults:
            error(part, "No content type in [Content_Types].xml")


def _check_package_relationships(archive: zipfile.ZipFile, error: Callable[[str, str], None]) -> None:
    try:
        relationships = _package_relationships(archive)
    except etree.XMLSyntaxError as exc:
        error("_rels/.rels", f"Not well-formed XML: {exc}")
        return
    if relationships is None:
        error("_rels/.rels", "Missing")
        return
    documents = [r for r in relationships if r.get("Type") == _DOCUMENT_RELATIONSHIP]
    if len(documents) != 1:
        error("_rels/.rels", f"Expected one {_DOCUMENT_RELATIONSHIP} relationship, found {len(documents)}")
    elif (
        documents[0].get("TargetMode") == "External"
        or _relationship_target_part(documents[0].get("Target", "")) != "document.xml"
    ):
        error("_rels/.rels", f"The {_DOCUMENT_RELATIONSHIP} relationship must target document.xml")


def _check_positional_parts(root: etree._Element, parts: list[str], error: Callable[[str, str], None]) -> None:
    pages, tracks = _page_count(root), len(_tracks(root))
    media: dict[tuple[str, str], str] = {}
    for part in sorted(parts):
        page = _PAGE_RE.fullmatch(part)
        track_media = _TRACK_MEDIA_RE.fullmatch(part)
        if page and int(page[1]) > pages:
            error(part, f"Image of page {page[1]}, but the document has {pages} page(s)")
        elif track_media:
            kind, number = track_media[1], track_media[2]
            if int(number) > tracks:
                error(part, f"Whole-track media for <track> {number}, but the document has {tracks} <track>(s)")
            first = media.setdefault((kind, number), part)
            if first != part:
                error(part, f"More than one {kind} file for <track> {number} (also {first})")


def _check_references(
    root: etree._Element,
    parts: list[str],
    relationship_targets: set[str],
    error: Callable[[str, str], None],
    warning: Callable[[str, str], None],
) -> None:
    sources, links = _markup_references(root)
    for part in sorted(sources.difference(parts)):
        error("document.xml", f"The <src> URI of {part!r} does not resolve to a part of the archive")
    accounted = sources | links | relationship_targets
    for part in parts:
        if not (
            part == "[Content_Types].xml"
            or part in accounted
            or any(pattern.fullmatch(part) for pattern in (_RELATIONSHIP_PART_RE, _PAGE_RE, _TRACK_MEDIA_RE))
        ):
            warning(part, "Not referenced by the markup or a relationship, nor a page image or whole-track media")


def _check_source(archive: zipfile.ZipFile, parts: list[str], error: Callable[[str, str], None]) -> None:
    """The rules on the original source and its descriptor (their content types are checked with all parts')."""
    try:
        relationships = _package_relationships(archive) or []
    except etree.XMLSyntaxError:
        return  # reported with the package relationships
    by_type: dict[str, list[etree._Element]] = {}
    for relationship in relationships:
        by_type.setdefault(relationship.get("Type", ""), []).append(relationship)
    for relationship_type, label in (
        (_SOURCE_RELATIONSHIP, "source"),
        (_SOURCE_METADATA_RELATIONSHIP, "source descriptor"),
    ):
        found = by_type.get(relationship_type, [])
        if len(found) > 1:
            error("_rels/.rels", f"More than one {relationship_type} relationship")
        for relationship in found:
            if relationship.get("TargetMode") == "External":
                error("_rels/.rels", f"The {label} relationship must target a part of the archive")
                continue
            part = _relationship_target_part(relationship.get("Target", ""))
            if part not in parts:
                error("_rels/.rels", f"The {label} part {part!r} is missing")
                continue
            if relationship_type == _SOURCE_METADATA_RELATIONSHIP:
                try:
                    root = _parse_xml(archive.read(part))
                except etree.XMLSyntaxError as exc:
                    error(part, f"Not well-formed XML: {exc}")
                    continue
                if root.tag != f"{{{_SOURCE_METADATA_NAMESPACE}}}source":
                    error(part, f"The root element must be source in the namespace {_SOURCE_METADATA_NAMESPACE}")
    if _SOURCE_METADATA_RELATIONSHIP in by_type and _SOURCE_RELATIONSHIP not in by_type:
        error("_rels/.rels", "A source-metadata relationship without a source relationship")


def _relationship_targets(path: Union[str, Path]) -> set[str]:
    """The parts targeted by relationships, apart from the main document (e.g. the original source)."""
    with zipfile.ZipFile(path) as archive:
        return _relationship_targets_of_parts(archive, archive.namelist()) - {"document.xml"}


def _renamed_opc_metadata(archive: zipfile.ZipFile, renames: Mapping[str, str | None]) -> dict[str, bytes]:
    """``_rels/.rels`` and ``[Content_Types].xml`` updated for the parts in ``renames`` (relationship targets and
    ``<Override>`` part names follow a renamed part; an ``<Override>`` of a removed part is dropped). Only the
    ones that change are returned; ones that are not well-formed are left alone."""
    updated: dict[str, bytes] = {}
    names = set(archive.namelist())
    if "_rels/.rels" in names:
        try:
            root = _parse_xml(archive.read("_rels/.rels"))
        except etree.XMLSyntaxError:
            root = None
        changed = False
        for relationship in [] if root is None else root.iterfind(f"{{{_RELATIONSHIPS_NAMESPACE}}}Relationship"):
            target = relationship.get("Target", "")
            if relationship.get("TargetMode") == "External":
                continue
            new = renames.get(_relationship_target_part(target))
            if new is not None:
                relationship.set("Target", f"/{new}" if target.startswith("/") else new)
                changed = True
        if changed:
            updated["_rels/.rels"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    if "[Content_Types].xml" in names:
        try:
            root = _parse_xml(archive.read("[Content_Types].xml"))
        except etree.XMLSyntaxError:
            root = None
        lowered = {old.lower(): new for old, new in renames.items()}
        changed = False
        for override in [] if root is None else list(root.iterfind(f"{{{_CONTENT_TYPES_NAMESPACE}}}Override")):
            part = override.get("PartName", "").lstrip("/").lower()
            if part not in lowered:
                continue
            if lowered[part] is None:
                root.remove(override)
            else:
                override.set("PartName", f"/{lowered[part]}")
            changed = True
        if changed:
            updated["[Content_Types].xml"] = etree.tostring(root, xml_declaration=True, encoding="UTF-8")
    return updated
