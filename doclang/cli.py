"""
DocLang CLI - Command-line interface for XML validation.

Provides a user-friendly CLI using Typer for validating DocLang XML documents
against XSD schemas and Schematron rules.
"""

from pathlib import Path
from typing import Optional
from enum import Enum

import typer
from rich.console import Console
from rich.table import Table

from doclang.xsd_validation import _validate_xsd
from doclang.schematron_validation import _validate_with_schematron
from doclang.utils import _VERSION

app = typer.Typer(
    name="doclang",
    help="DocLang XML validation tool with XSD and Schematron support",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()


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
    allow_empty_namespace: bool = typer.Option(False, "--allow-empty-namespace", "-n", help="Allow documents without namespace (auto-inject DocLang namespace)"),
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
    # Use bundled schemas if not provided
    try:
        bundled_xsd, bundled_sch = _get_bundled_schema_files()
    except FileNotFoundError as e:
        console.print(f"[red]Error: {e}[/red]")
        raise typer.Exit(1)

    if not xsd:
        xsd = bundled_xsd
    if not sch:
        sch = bundled_sch

    if not quiet and format == OutputFormat.text:
        console.print(f"[bold]Validating:[/bold] {xml_file}")
        console.print("─" * 60)

    results = {
        "file": str(xml_file),
        "xsd": {"valid": True, "errors": []},
        "schematron": {"valid": True, "errors": []},
    }

    # XSD Validation
    if not schematron_only and xsd:
        if verbose:
            console.print(f"[bold]XSD Validation[/bold]")
            console.print(f"Schema: {xsd}")

        xsd_valid, xsd_errors = _validate_xsd(xml_file, xsd, allow_empty_namespace)
        results["xsd"]["valid"] = xsd_valid
        results["xsd"]["errors"] = xsd_errors

        if not quiet and format == OutputFormat.text:
            if xsd_valid:
                console.print("[green]✓[/green] XSD validation passed")
            else:
                console.print("[red]✗[/red] XSD validation failed")
                for error in xsd_errors:
                    if "line" in error:
                        console.print(f"  Line {error['line']}: {error['message']}")
                    else:
                        console.print(f"  {error.get('error', 'Unknown error')}")

        if not xsd_valid and not xsd_only:
            if format == OutputFormat.json:
                console.print_json(data=results)
            raise typer.Exit(1)

    # Schematron Validation
    if not xsd_only and sch:
        try:
            if verbose:
                console.print(f"[bold]Schematron Validation[/bold]")
                console.print(f"Schema: {sch}")

            is_valid, failed_asserts = _validate_with_schematron(
                xml_file,
                sch_file=sch,
                allow_empty_namespace=allow_empty_namespace,
                verbose=verbose
            )
            results["schematron"]["valid"] = is_valid

            # Convert failed_asserts to error dicts
            if not is_valid:
                sch_errors = [
                    {
                        "location": assert_elem.get("location", "unknown"),
                        "message": assert_elem.find("{http://purl.oclc.org/dsdl/svrl}text").text
                        if assert_elem.find("{http://purl.oclc.org/dsdl/svrl}text") is not None
                        else "No message"
                    }
                    for assert_elem in failed_asserts
                ]
                results["schematron"]["errors"] = sch_errors
            else:
                results["schematron"]["errors"] = []

            if not quiet and format == OutputFormat.text:
                if is_valid:
                    console.print("[green]✓[/green] Schematron validation passed")
                else:
                    console.print("[red]✗[/red] Schematron validation failed")
                    for error in results["schematron"]["errors"]:
                        console.print(f"  {error['location']}")
                        console.print(f"    {error['message']}")

        except Exception as e:
            results["schematron"]["valid"] = False
            results["schematron"]["errors"] = [{"error": str(e)}]
            if not quiet and format == OutputFormat.text:
                console.print(f"[red]✗[/red] Schematron validation error: {e}")

    # Output results
    if format == OutputFormat.json:
        console.print_json(data=results)
    elif not quiet:
        console.print("─" * 60)
        if results["xsd"]["valid"] and results["schematron"]["valid"]:
            console.print("[bold green]✓ VALIDATION SUCCESSFUL[/bold green]")
        else:
            console.print("[bold red]✗ VALIDATION FAILED[/bold red]")

    # Exit with appropriate code
    if not results["xsd"]["valid"] or not results["schematron"]["valid"]:
        raise typer.Exit(1)


def version_callback(value: bool):
    """Show version and exit."""
    if value:
        console.print(f"doclang version {_VERSION}")
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
    pass


if __name__ == "__main__":
    app()
