"""Internal implementation for DocLang archive packaging."""

from __future__ import annotations

import shutil
import tempfile
import zipfile
from collections.abc import Mapping, Sequence
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


def _place_pages(stage: Path, pages: PagesInput) -> None:
    pages_dir = stage / "pages"
    if isinstance(pages, Mapping):
        for page_number, source in pages.items():
            if not isinstance(page_number, int) or page_number < 1:
                raise PackagingError(f"Page numbers must be positive integers, got {page_number!r}")
            source_path = Path(source)
            destination = pages_dir / f"{page_number}{source_path.suffix}"
            _copy_file(source_path, destination, label="Page file")
        return

    if isinstance(pages, str | Path):
        _copy_tree_into(Path(pages), pages_dir, label="Pages directory")
        return

    for index, source in enumerate(pages, start=1):
        source_path = Path(source)
        destination = pages_dir / f"{index}{source_path.suffix}"
        _copy_file(source_path, destination, label="Page file")


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
        _write_opc_metadata(stage)

        if validate:
            from doclang.validation import validate as validate_document

            validate_document(stage / "document.xml")

        _create_zip(stage, output_path)

    return output_path.resolve()
