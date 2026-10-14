"""Bundled DocLang schema paths and spec-version selection (internal).

``schemas/<MAJOR.MINOR>/`` holds the latest released schemas of each spec minor version.
The schemas directly in the package directory are the development head: they are used when no
version is specified, and as a fallback for a declared version that has no ``schemas/`` folder.
At release, the head is copied to ``schemas/<MAJOR.MINOR>/`` (see ``utils/prepare_release.py``).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

_SCHEMA_DIR = Path(__file__).resolve().parent
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)$")
_SCHEMA_VERSION_RE = re.compile(r'<xs:schema[^>]*\sversion="(\d+)\.(\d+)\.\d+"', re.DOTALL)


_XS_NS = "http://www.w3.org/2001/XMLSchema"


class UnsupportedVersionError(ValueError):
    """Raised when there are no schemas for a requested or declared DocLang spec version."""


@dataclass(frozen=True)
class SchemaSelection:
    """The schemas chosen for a document."""

    version: str  # version of the chosen schemas (for the head: its label)
    xsd: Path
    sch: Path
    declared: bool  # False when no version was requested or declared (head used)
    head_fallback_for: str | None = None  # declared version without schemas, for which the head was used


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


def _available_versions() -> list[str]:
    """Versions with bundled ``schemas/`` folders, oldest first."""
    versioned_dir = _SCHEMA_DIR / "schemas"
    if not versioned_dir.is_dir():
        return []
    versions = [e.name for e in versioned_dir.iterdir() if _VERSION_RE.match(e.name) and _has_versioned_schemas(e.name)]
    return sorted(versions, key=_version_key)


def _resolve_in_folders(requested: str) -> str | None:
    """Map a requested ``MAJOR.MINOR`` to a version with bundled schemas, or None.

    An exact match wins. From major version 1, an instance is compatible with any later minor
    of the same major, so the nearest newer minor with schemas is used.
    """
    if not _VERSION_RE.match(requested):
        return None
    available = _available_versions()
    if requested in available:
        return requested
    major, minor = _version_key(requested)
    if major >= 1:
        for candidate in available:
            if _version_key(candidate)[0] == major and _version_key(candidate)[1] > minor:
                return candidate
    return None


def _versioned_paths(version: str) -> tuple[Path, Path]:
    folder = _versioned_dir(version)
    return folder / "doclang.xsd", folder / "doclang.sch"


def _head_description() -> str:
    """How to refer to the head in messages: its version if identical to the released schema of that
    version, else "unreleased development version" (the head's label is then not reliable)."""
    label = _current_version()
    if _has_versioned_schemas(label):
        released_xsd, released_sch = _versioned_paths(label)
        head_xsd, head_sch = _bundled_schema_paths()
        if released_xsd.read_bytes() == head_xsd.read_bytes() and released_sch.read_bytes() == head_sch.read_bytes():
            return label
    return "unreleased development version"


def _enumerated_versions(xsd: Path) -> set[str]:
    """Versions the XSD enumerates for the root ``version`` attribute (empty if only format-constrained)."""
    parser = etree.XMLParser(resolve_entities=False, no_network=True)
    tree = etree.parse(str(xsd), parser)
    values = tree.xpath("//xs:attribute[@name='version']//xs:enumeration/@value", namespaces={"xs": _XS_NS})
    return {str(v) for v in values}  # type: ignore[union-attr]


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


def _select_schemas(
    xml_file: str | Path,
    spec_version: str | None = None,
    *,
    strict_declared_version: bool = False,
) -> SchemaSelection:
    """Pick schemas for a document.

    1. An explicit ``spec_version`` uses the bundled schemas of that version (else UnsupportedVersionError).
    2. Otherwise the document's declared ``version`` uses the bundled schemas of that version.
    3. Otherwise the development head is used. For a declared version without schemas this is a
       fallback, unless ``strict_declared_version`` is set (then UnsupportedVersionError).
    """
    if spec_version is not None:
        version = _resolve_in_folders(spec_version)
        if version is None:
            available = ", ".join(_available_versions()) or "none"
            raise UnsupportedVersionError(
                f"No schema for DocLang spec version '{spec_version}'; available versions: {available}"
            )
        xsd, sch = _versioned_paths(version)
        return SchemaSelection(version=version, xsd=xsd, sch=sch, declared=True)

    declared_version = _declared_version(xml_file)
    head_xsd, head_sch = _bundled_schema_paths()
    if declared_version is None:
        return SchemaSelection(version=_current_version(), xsd=head_xsd, sch=head_sch, declared=False)

    version = _resolve_in_folders(declared_version)
    if version is not None:
        xsd, sch = _versioned_paths(version)
        return SchemaSelection(version=version, xsd=xsd, sch=sch, declared=True)

    if strict_declared_version:
        available = ", ".join(_available_versions()) or "none"
        raise UnsupportedVersionError(
            f"No schema for declared DocLang version '{declared_version}'; available versions: {available}"
        )
    return SchemaSelection(
        version=_current_version(),
        xsd=head_xsd,
        sch=head_sch,
        declared=True,
        head_fallback_for=declared_version,
    )
