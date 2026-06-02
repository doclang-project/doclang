"""Bundled DocLang schema paths (internal)."""

from pathlib import Path

_SCHEMA_DIR = Path(__file__).resolve().parent


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
