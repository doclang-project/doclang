"""
DocLang CLI - Command-line interface for XML validation.

Provides a user-friendly CLI using Typer for validating DocLang XML documents
against XSD schemas and Schematron rules.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import typer

from doclang.schematron_validation import _validate_with_schematron
from doclang.utils import _VERSION
from doclang.xsd_validation import _validate_xsd

app = typer.Typer(
    name="doclang",
    help="DocLang XML validation tool with XSD and Schematron support",
    add_completion=False,
    no_args_is_help=True,
)


class OutputFormat(str, Enum):
    """Output format options."""

    text = "text"
    json = "json"


def _get_bundled_schema_files() -> tuple[Path, Path]:
    """
    Get paths to bundled XSD and Schematron files.

    Returns:
        tuple: (xsd_file, sch_file) paths to bundled schemas
    """
    schema_dir = Path(__file__).parent
    xsd_file = schema_dir / "doclang.xsd"
    sch_file = schema_dir / "doclang.sch"

    if not xsd_file.exists():
        raise FileNotFoundError(f"Bundled XSD schema not found: {xsd_file}")
    if not sch_file.exists():
        raise FileNotFoundError(f"Bundled Schematron schema not found: {sch_file}")

    return xsd_file, sch_file


@app.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)
def validate(
    xml_file: Path = typer.Argument(..., help="XML file to validate", exists=True),
    xsd: Optional[Path] = typer.Option(None, help="XSD schema file (uses bundled schema if not provided)"),
    sch: Optional[Path] = typer.Option(None, help="Schematron rules file (uses bundled schema if not provided)"),
    xsd_only: bool = typer.Option(False, "--xsd-only", help="Validate XSD only"),
    schematron_only: bool = typer.Option(False, "--schematron-only", help="Validate Schematron only"),
    allow_empty_namespace: bool = typer.Option(
        False,
        "--allow-empty-namespace",
        "-n",
        help="Allow documents without namespace (auto-inject DocLang namespace)",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode (exit code only)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    format: OutputFormat = typer.Option(OutputFormat.text, "--format", "-f", help="Output format"),
):
    """
    Validate XML document against XSD schema and Schematron rules.

    Uses bundled DocLang schemas by default. You can override with custom schemas.

    Examples:

        # Basic validation (uses bundled schemas)
        doclang validate document.xml

        # Custom schema paths
        doclang validate document.xml --xsd custom.xsd --sch custom.sch

        # XSD only
        doclang validate document.xml --xsd-only

        # JSON output
        doclang validate document.xml --format json
    """
    try:
        bundled_xsd, bundled_sch = _get_bundled_schema_files()
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    if not xsd:
        xsd = bundled_xsd
    if not sch:
        sch = bundled_sch

    if not quiet and format == OutputFormat.text:
        typer.echo(f"Validating: {xml_file}")
        typer.echo("-" * 60)

    results: dict[str, Any] = {
        "file": str(xml_file),
        "xsd": {"valid": True, "errors": []},
        "schematron": {"valid": True, "errors": []},
    }

    if not schematron_only and xsd:
        if verbose:
            typer.echo("XSD Validation")
            typer.echo(f"Schema: {xsd}")

        xsd_valid, xsd_errors = _validate_xsd(xml_file, xsd, allow_empty_namespace)
        results["xsd"]["valid"] = xsd_valid
        results["xsd"]["errors"] = xsd_errors

        if not quiet and format == OutputFormat.text:
            if xsd_valid:
                typer.echo("XSD validation passed")
            else:
                typer.echo("XSD validation failed")
                for error in xsd_errors:
                    if "line" in error:
                        typer.echo(f"  Line {error['line']}: {error['message']}")
                    else:
                        typer.echo(f"  {error.get('error', 'Unknown error')}")

        if not xsd_valid and not xsd_only:
            if format == OutputFormat.json:
                typer.echo(json.dumps(results, indent=2))
            raise typer.Exit(1)

    if not xsd_only and sch:
        try:
            if verbose:
                typer.echo("Schematron Validation")
                typer.echo(f"Schema: {sch}")

            is_valid, failed_asserts = _validate_with_schematron(
                xml_file,
                sch_file=sch,
                allow_empty_namespace=allow_empty_namespace,
                verbose=verbose,
            )
            results["schematron"]["valid"] = is_valid

            if not is_valid:
                sch_errors = [
                    {
                        "location": assert_elem.get("location", "unknown"),
                        "message": assert_elem.find("{http://purl.oclc.org/dsdl/svrl}text").text
                        if assert_elem.find("{http://purl.oclc.org/dsdl/svrl}text") is not None
                        else "No message",
                    }
                    for assert_elem in failed_asserts
                ]
                results["schematron"]["errors"] = sch_errors
            else:
                results["schematron"]["errors"] = []

            if not quiet and format == OutputFormat.text:
                if is_valid:
                    typer.echo("Schematron validation passed")
                else:
                    typer.echo("Schematron validation failed")
                    for error in results["schematron"]["errors"]:
                        typer.echo(f"  {error['location']}")
                        typer.echo(f"    {error['message']}")

        except Exception as exc:
            results["schematron"]["valid"] = False
            results["schematron"]["errors"] = [{"error": str(exc)}]
            if not quiet and format == OutputFormat.text:
                typer.echo(f"Schematron validation error: {exc}")

    if format == OutputFormat.json:
        typer.echo(json.dumps(results, indent=2))
    elif not quiet:
        typer.echo("-" * 60)
        if results["xsd"]["valid"] and results["schematron"]["valid"]:
            typer.echo("VALIDATION SUCCESSFUL")
        else:
            typer.echo("VALIDATION FAILED")

    if not results["xsd"]["valid"] or not results["schematron"]["valid"]:
        raise typer.Exit(1)


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        typer.echo(f"doclang version {_VERSION}")
        raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        None,
        "--version",
        "-v",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """DocLang XML validation tool."""


if __name__ == "__main__":
    app()
