"""Bundled DocLang schema paths and spec-version selection (internal).

``schemas/<MAJOR.MINOR>/`` holds the latest released schemas of each spec minor version.
The schemas directly in the package directory are the development head: they are used when no
version is specified, and for a version that has no ``schemas/`` folder yet. At release, the head
is copied to ``schemas/<MAJOR.MINOR>/`` (see ``utils/prepare_release.py``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

_SCHEMA_DIR = Path(__file__).resolve().parent
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)$")
_SCHEMA_VERSION_RE = re.compile(r'<xs:schema[^>]*\sversion="(\d+)\.(\d+)\.\d+"', re.DOTALL)


class UnsupportedVersionError(ValueError):
    """Raised when a requested DocLang spec version is not supported by this toolkit."""


@dataclass(frozen=True)
class SchemaSelection:
    """The schemas chosen for a document."""

    version: str
    xsd: Path
    sch: Path
    declared: bool  # False when no version was requested or declared (latest assumed)


def _bundled_xsd_path() -> Path:
    path = _SCHEMA_DIR / "doclang.xsd"
    if not path.exists():
        raise FileNotFoundError(f"Bundled XSD schema not found: {path}")
    return path


def _bundled_sch_path() -> Path:
    path = _SCHEMA_DIR / "doclang.sch"
    if not path.exists():
        raise FileNotFoundError(f"Bundled Schematron schema not found: {path}")
    return path


def _bundled_schema_paths() -> tuple[Path, Path]:
    return _bundled_xsd_path(), _bundled_sch_path()


def _version_key(version: str) -> tuple[int, int]:
    match = _VERSION_RE.match(version)
    assert match is not None
    return int(match.group(1)), int(match.group(2))


def _schema_version(xsd: Path) -> str:
    """The ``MAJOR.MINOR`` spec version of an XSD, from its ``xs:schema`` version attribute."""
    match = _SCHEMA_VERSION_RE.search(xsd.read_text(encoding="utf-8"))
    if match is None:
        raise FileNotFoundError(f"No schema version found in {xsd}")
    return f"{match.group(1)}.{match.group(2)}"


def _current_version() -> str:
    """The spec version of the top-level (latest) schemas."""
    return _schema_version(_bundled_xsd_path())


def _versioned_dir(version: str) -> Path:
    return _SCHEMA_DIR / "schemas" / version


def _has_versioned_schemas(version: str) -> bool:
    folder = _versioned_dir(version)
    return (folder / "doclang.xsd").exists() and (folder / "doclang.sch").exists()


def _supported_versions() -> list[str]:
    """All supported spec versions, oldest first."""
    versions = {_current_version()}
    versioned_dir = _SCHEMA_DIR / "schemas"
    if versioned_dir.is_dir():
        versions.update(
            entry.name
            for entry in versioned_dir.iterdir()
            if _VERSION_RE.match(entry.name) and _has_versioned_schemas(entry.name)
        )
    return sorted(versions, key=_version_key)


def _resolve_version(requested: str) -> str:
    """Map a requested ``MAJOR.MINOR`` to a supported version, or raise UnsupportedVersionError.

    An exact match wins. From major version 1, an instance is compatible with any later minor
    of the same major, so the nearest newer supported minor is used.
    """
    supported = _supported_versions()
    if _VERSION_RE.match(requested):
        if requested in supported:
            return requested
        major, minor = _version_key(requested)
        if major >= 1:
            for candidate in supported:
                if _version_key(candidate)[0] == major and _version_key(candidate)[1] > minor:
                    return candidate
    raise UnsupportedVersionError(
        f"Unsupported DocLang spec version '{requested}'; supported versions: {', '.join(supported)}"
    )


def _schema_paths_for(version: str) -> tuple[Path, Path]:
    """Released schemas of ``version`` if bundled, else the development head (if it is that version)."""
    if _has_versioned_schemas(version):
        folder = _versioned_dir(version)
        return folder / "doclang.xsd", folder / "doclang.sch"
    return _bundled_schema_paths()


def _declared_version(xml_file: str | Path) -> str | None:
    """The ``version`` attribute of the root element, or None if absent or unreadable."""
    try:
        with open(xml_file, "rb") as f:
            _, root = next(
                etree.iterparse(f, events=("start",), resolve_entities=False, no_network=True, load_dtd=False)
            )
            return root.get("version")
    except Exception:
        return None


def _select_schemas(xml_file: str | Path, spec_version: str | None = None) -> SchemaSelection:
    """Pick schemas: explicit ``spec_version``, else the document's ``version``, else the latest."""
    requested = spec_version if spec_version is not None else _declared_version(xml_file)
    if requested is None:
        version = _current_version()
        xsd, sch = _bundled_schema_paths()
        return SchemaSelection(version=version, xsd=xsd, sch=sch, declared=False)
    version = _resolve_version(requested)
    xsd, sch = _schema_paths_for(version)
    return SchemaSelection(version=version, xsd=xsd, sch=sch, declared=True)
