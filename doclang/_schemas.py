"""Bundled DocLang schema paths and spec-version selection (internal).

The schemas for the current spec version live directly in the package directory.
Schemas for other supported ``MAJOR.MINOR`` versions live in ``schemas/<MAJOR.MINOR>/``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from lxml import etree

_SCHEMA_DIR = Path(__file__).resolve().parent
_VERSION_RE = re.compile(r"^(\d+)\.(\d+)$")
_ENUM_RE = re.compile(r'<xs:enumeration value="(\d+\.\d+)"/>')


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


def _current_version() -> str:
    """The spec version of the top-level (latest) schemas, from the XSD version enumeration."""
    versions = _ENUM_RE.findall(_bundled_xsd_path().read_text(encoding="utf-8"))
    if not versions:
        raise FileNotFoundError(f"No spec version found in {_bundled_xsd_path()}")
    return max(versions, key=_version_key)


def _supported_versions() -> list[str]:
    """All supported spec versions, oldest first."""
    versions = {_current_version()}
    versioned_dir = _SCHEMA_DIR / "schemas"
    if versioned_dir.is_dir():
        for entry in versioned_dir.iterdir():
            if _VERSION_RE.match(entry.name) and (entry / "doclang.xsd").exists() and (entry / "doclang.sch").exists():
                versions.add(entry.name)
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
    if version == _current_version():
        return _bundled_schema_paths()
    folder = _SCHEMA_DIR / "schemas" / version
    return folder / "doclang.xsd", folder / "doclang.sch"


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
