"""
DocLang CLI - Command-line interface for XML validation.

Provides a user-friendly CLI using Typer for validating DocLang XML documents
against XSD schemas and Schematron rules.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any

import typer

from doclang._schemas import _bundled_schema_paths
from doclang.utils import _VERSION
from doclang.validation import ValidationError
from doclang.validation import validate as validate_document

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


@app.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)
def validate(
    xml_file: Path = typer.Argument(..., help="XML file to validate", exists=True),
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
    Validate XML document against bundled XSD schema and Schematron rules.

    Examples:

        doclang validate document.xml
        doclang validate document.xml --xsd-only
        doclang validate document.xml --format json
    """
    try:
        bundled_xsd, bundled_sch = _bundled_schema_paths()
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    if not quiet and format == OutputFormat.text:
        typer.echo(f"Validating: {xml_file}")
        typer.echo("-" * 60)

    try:
        validate_document(
            xml_file,
            allow_empty_namespace=allow_empty_namespace,
            xsd_only=xsd_only,
            schematron_only=schematron_only,
        )
    except ValidationError as exc:
        results: dict[str, Any] = {
            "file": exc.file,
            "xsd": {"valid": exc.xsd_valid, "errors": exc.xsd_errors},
            "schematron": {"valid": exc.schematron_valid, "errors": exc.schematron_errors},
        }

        if not quiet and format == OutputFormat.text:
            if not schematron_only:
                if verbose:
                    typer.echo("XSD Validation")
                    typer.echo(f"Schema: {bundled_xsd}")
                if exc.xsd_valid:
                    typer.echo("XSD validation passed")
                else:
                    typer.echo("XSD validation failed")
                    for error in exc.xsd_errors:
                        if "line" in error:
                            typer.echo(f"  Line {error['line']}: {error['message']}")
                        else:
                            typer.echo(f"  {error.get('error', 'Unknown error')}")

            if not xsd_only and (exc.xsd_valid or schematron_only):
                if verbose:
                    typer.echo("Schematron Validation")
                    typer.echo(f"Schema: {bundled_sch}")
                if exc.schematron_valid:
                    typer.echo("Schematron validation passed")
                else:
                    typer.echo("Schematron validation failed")
                    for error in exc.schematron_errors:
                        typer.echo(f"  {error['location']}")
                        typer.echo(f"    {error['message']}")

        if format == OutputFormat.json:
            typer.echo(json.dumps(results, indent=2))
        elif not quiet:
            typer.echo("-" * 60)
            typer.echo("VALIDATION FAILED")

        raise typer.Exit(1)

    if not quiet and format == OutputFormat.text:
        if not schematron_only:
            if verbose:
                typer.echo("XSD Validation")
                typer.echo(f"Schema: {bundled_xsd}")
            typer.echo("XSD validation passed")

        if not xsd_only:
            if verbose:
                typer.echo("Schematron Validation")
                typer.echo(f"Schema: {bundled_sch}")
            typer.echo("Schematron validation passed")

    if format == OutputFormat.json:
        typer.echo(
            json.dumps(
                {
                    "file": str(xml_file),
                    "xsd": {"valid": True, "errors": []},
                    "schematron": {"valid": True, "errors": []},
                },
                indent=2,
            )
        )
    elif not quiet:
        typer.echo("-" * 60)
        typer.echo("VALIDATION SUCCESSFUL")


def _version_callback(value: bool):
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
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
):
    """DocLang XML validation tool."""


if __name__ == "__main__":
    app()
