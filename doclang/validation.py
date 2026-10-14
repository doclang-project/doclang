"""Public validation API for DocLang XML documents."""

import warnings
from pathlib import Path
from typing import Any, Union

from doclang._schemas import (
    UnsupportedVersionError,
    _declared_version,
    _enumerated_versions,
    _head_description,
    _select_schemas,
)
from doclang.schematron import (
    SchematronBackendNotFound,
    SchematronValidator,
    SchematronViolation,
    _default_schematron_validator,
)
from doclang.xsd_validation import _validate_xsd

__all__ = ["SchematronBackendNotFound", "UnsupportedVersionError", "ValidationError", "VersionNote", "validate"]


def _violations_to_errors(violations: list[SchematronViolation]) -> list[dict[str, Any]]:
    return [
        {
            "location": violation.location or "unknown",
            "message": violation.message,
        }
        for violation in violations
    ]


class VersionNote(UserWarning):
    """Explains a version-related adjustment made during validation (see ``validate()``)."""


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
    strict_xsd_version_attr: bool = False,
    strict_declared_version: bool = False,
) -> None:
    """Validate a DocLang XML file using the bundled reference XSD and Schematron rules.

    The spec version to validate against is ``spec_version`` if given, else the ``version``
    attribute of the root element. If neither is set the version is unspecified: the latest schema
    (the development head) is used and a :class:`UserWarning` is issued. The same happens, with a
    warning, for a declared version that has no bundled schema; pass ``strict_declared_version=True``
    to fail instead.

    Some XSDs (currently 0.7) only accept their own version in the root ``version`` attribute. If the
    declared version differs, it is by default replaced by the schema's version in memory for XSD
    validation (the file is not modified) and a :class:`VersionNote` is issued. Pass
    ``strict_xsd_version_attr=True`` to apply the XSD's own check as is, i.e. fail in that case.

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
        selection = _select_schemas(path, spec_version, strict_declared_version=strict_declared_version)
    except UnsupportedVersionError as exc:
        if spec_version is not None:
            raise
        raise ValidationError(xsd_errors=[{"error": str(exc)}], schematron_errors=[]) from exc
    declared_version = _declared_version(path)
    # Schemas that enumerate the allowed `version` values (0.7) would reject a differing declared
    # version on that attribute alone; for those the declared version is replaced in memory.
    enumerated_versions = _enumerated_versions(selection.xsd)
    rewrite_declared_version = (
        not strict_xsd_version_attr
        and declared_version is not None
        and bool(enumerated_versions)
        and declared_version not in enumerated_versions
    )
    if spec_version is not None and declared_version is not None and declared_version != spec_version:
        warnings.warn(
            f"Document declares version {declared_version}; validating as {selection.version} as requested.",
            UserWarning,
            stacklevel=2,
        )
        if rewrite_declared_version:
            warnings.warn(
                f'The {selection.version} XSD only accepts version "{selection.version}". Under strict validation, '
                f"a {declared_version} document would therefore fail on the version attribute alone. "
                f'To validate all other rules, the declared version is replaced with "{selection.version}" in memory '
                "(the file is not modified). The declared version itself is not checked. "
                "Use --strict-xsd-version-attr (strict_xsd_version_attr=True in Python) to apply the XSD's "
                "version check as is.",
                VersionNote,
                stacklevel=2,
            )
    elif not selection.declared:
        warnings.warn(
            f"No DocLang version declared; validating against the latest schema ({_head_description()}).",
            UserWarning,
            stacklevel=2,
        )
    elif selection.head_fallback_for is not None:
        warnings.warn(
            f"No schema for declared DocLang version {selection.head_fallback_for}; "
            f"validating against the latest schema ({_head_description()}).",
            UserWarning,
            stacklevel=2,
        )

    if not schematron_only:
        xsd_errors = _validate_xsd(
            path,
            allow_empty_namespace=allow_empty_namespace,
            xsd_file=selection.xsd,
            schema_version=selection.version if rewrite_declared_version else None,
        )

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
