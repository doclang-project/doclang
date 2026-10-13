"""Public validation API for DocLang XML documents."""

import warnings
from pathlib import Path
from typing import Any, Union

from doclang._schemas import UnsupportedVersionError, _declared_version, _select_schemas
from doclang.schematron import (
    SchematronBackendNotFound,
    SchematronValidator,
    SchematronViolation,
    _default_schematron_validator,
)
from doclang.xsd_validation import _validate_xsd

__all__ = ["SchematronBackendNotFound", "UnsupportedVersionError", "ValidationError", "validate"]


def _violations_to_errors(violations: list[SchematronViolation]) -> list[dict[str, Any]]:
    return [
        {
            "location": violation.location or "unknown",
            "message": violation.message,
        }
        for violation in violations
    ]


class ValidationError(Exception):
    """Raised when DocLang XML validation fails."""

    def __init__(
        self,
        *,
        xsd_errors: list[dict[str, Any]],
        schematron_errors: list[dict[str, Any]],
    ) -> None:
        self.xsd_errors = xsd_errors
        self.schematron_errors = schematron_errors
        super().__init__(self._format_message())

    def _format_message(self) -> str:
        lines: list[str] = []
        if self.xsd_errors:
            lines.append("XSD validation failed:")
            for error in self.xsd_errors:
                if "line" in error:
                    lines.append(f"  Line {error['line']}: {error['message']}")
                else:
                    lines.append(f"  {error.get('error', 'Unknown error')}")
        if self.schematron_errors:
            lines.append("Schematron validation failed:")
            for error in self.schematron_errors:
                if "location" in error:
                    lines.append(f"  {error['location']}: {error['message']}")
                else:
                    lines.append(f"  {error.get('error', 'Unknown error')}")
        return "\n".join(lines)


def validate(
    xml_file: Union[str, Path],
    *,
    allow_empty_namespace: bool = False,
    xsd_only: bool = False,
    schematron_only: bool = False,
    schematron: SchematronValidator | None = None,
    spec_version: str | None = None,
) -> None:
    """Validate a DocLang XML file using the bundled reference XSD and Schematron rules.

    The spec version to validate against is ``spec_version`` if given, else the ``version``
    attribute of the root element. If neither is set the version is unspecified: the latest
    supported version is used and a :class:`UserWarning` is issued.

    By default both XSD and Schematron validation run. Pass ``schematron`` to use a
    custom Schematron backend; when omitted, the default Saxon/C backend is used
    (requires ``doclang[schematron-saxon]``).

    Raises :class:`ValidationError` on failure, including when the document declares a
    version that is not supported.
    Raises :class:`UnsupportedVersionError` when ``spec_version`` is not supported.
    Raises :class:`SchematronBackendNotFound` when Schematron validation is requested
    but no backend is available.
    """
    path = Path(xml_file)
    xsd_errors: list[dict[str, Any]] = []
    schematron_errors: list[dict[str, Any]] = []

    try:
        selection = _select_schemas(path, spec_version)
    except UnsupportedVersionError as exc:
        if spec_version is not None:
            raise
        raise ValidationError(xsd_errors=[{"error": str(exc)}], schematron_errors=[]) from exc
    if spec_version is not None:
        declared = _declared_version(path)
        if declared is not None and declared != spec_version:
            warnings.warn(
                f"Document declares version {declared}; validating as {selection.version} as requested.",
                UserWarning,
                stacklevel=2,
            )
    elif not selection.declared:
        warnings.warn(
            f"No DocLang version declared; validating against the latest supported version ({selection.version}).",
            UserWarning,
            stacklevel=2,
        )

    if not schematron_only:
        xsd_errors = _validate_xsd(path, allow_empty_namespace=allow_empty_namespace, xsd_file=selection.xsd)

    if not xsd_only:
        validator = schematron or _default_schematron_validator()
        try:
            violations = validator.validate(
                path,
                schema_path=selection.sch,
                allow_empty_namespace=allow_empty_namespace,
            )
            if violations:
                schematron_errors = _violations_to_errors(violations)
        except SchematronBackendNotFound:
            raise
        except Exception as exc:
            schematron_errors = [{"error": str(exc)}]

    if xsd_errors or schematron_errors:
        raise ValidationError(
            xsd_errors=xsd_errors,
            schematron_errors=schematron_errors,
        )
