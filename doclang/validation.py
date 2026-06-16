"""Public validation API for DocLang XML documents."""

from pathlib import Path
from typing import Any, Union

from doclang.schematron_validation import _validate_with_schematron
from doclang.xsd_validation import _validate_xsd

__all__ = ["ValidationError", "validate"]

_SVRL_NS = "http://purl.oclc.org/dsdl/svrl"


def _failed_asserts_to_errors(failed_asserts: list) -> list[dict[str, Any]]:
    return [
        {
            "location": assert_elem.get("location", "unknown"),
            "message": assert_elem.find(f"{{{_SVRL_NS}}}text").text
            if assert_elem.find(f"{{{_SVRL_NS}}}text") is not None
            else "No message",
        }
        for assert_elem in failed_asserts
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
) -> None:
    """Validate a DocLang XML file using the bundled reference XSD and Schematron rules.

    Raises :class:`ValidationError` on failure.
    """
    path = Path(xml_file)
    xsd_errors: list[dict[str, Any]] = []
    schematron_errors: list[dict[str, Any]] = []

    if not schematron_only:
        xsd_errors = _validate_xsd(path, allow_empty_namespace=allow_empty_namespace)

    if not xsd_only:
        try:
            failed_asserts = _validate_with_schematron(
                path,
                allow_empty_namespace=allow_empty_namespace,
                verbose=False,
            )
            if failed_asserts:
                schematron_errors = _failed_asserts_to_errors(failed_asserts)
        except Exception as exc:
            schematron_errors = [{"error": str(exc)}]

    if xsd_errors or schematron_errors:
        raise ValidationError(
            xsd_errors=xsd_errors,
            schematron_errors=schematron_errors,
        )
