"""Schematron validation plug-in interface."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class SchematronViolation:
    """A single Schematron rule failure."""

    message: str
    location: str | None = None
    rule_id: str | None = None
    test: str | None = None


@runtime_checkable
class SchematronValidator(Protocol):
    """Validate DocLang XML against a Schematron schema."""

    def validate(
        self,
        xml_path: Path,
        *,
        schema_path: Path,
        allow_empty_namespace: bool = False,
    ) -> list[SchematronViolation]:
        """Return rule violations; an empty list means validation passed."""


class SchematronBackendNotFound(ImportError):
    """Raised when Schematron validation is requested but no backend is available."""

    def __init__(self) -> None:
        super().__init__(
            "Schematron validation requires a backend. Install doclang[schematron-saxon] "
            "or pass schematron=YourValidator() to validate()."
        )


def _require_saxonche_backend() -> None:
    """Raise SchematronBackendNotFound when the optional saxonche dependency is missing."""
    try:
        import saxonche  # noqa: F401
    except ImportError as exc:
        raise SchematronBackendNotFound() from exc


def _default_schematron_validator() -> SchematronValidator:
    _require_saxonche_backend()
    try:
        from doclang.backends.saxonche import SaxoncheValidator
    except ImportError as exc:
        raise SchematronBackendNotFound() from exc
    return SaxoncheValidator()
