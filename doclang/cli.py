"""
DocLang CLI - Command-line interface for the DocLang toolkit.

Provides a user-friendly CLI using Typer for working with DocLang documents.
"""

import json
from enum import Enum
from pathlib import Path
from typing import Any

import typer

from doclang._schemas import _bundled_schema_paths
from doclang.packaging import PackagingError
from doclang.packaging import pack as pack_document
from doclang.utils import _VERSION
from doclang.validation import ValidationError
from doclang.validation import validate as validate_document

app = typer.Typer(
    name="doclang",
    help="DocLang toolkit",
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
            "xsd": {"valid": not exc.xsd_errors, "errors": exc.xsd_errors},
            "schematron": {"valid": not exc.schematron_errors, "errors": exc.schematron_errors},
        }

        if not quiet and format == OutputFormat.text:
            if not schematron_only:
                if verbose:
                    typer.echo("XSD Validation")
                    typer.echo(f"Schema: {bundled_xsd}")
                if not exc.xsd_errors:
                    typer.echo("XSD validation passed")
                else:
                    typer.echo("XSD validation failed")
                    for error in exc.xsd_errors:
                        if "line" in error:
                            typer.echo(f"  Line {error['line']}: {error['message']}")
                        else:
                            typer.echo(f"  {error.get('error', 'Unknown error')}")

            if not xsd_only:
                if verbose:
                    typer.echo("Schematron Validation")
                    typer.echo(f"Schema: {bundled_sch}")
                if not exc.schematron_errors:
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
                    "xsd": {"valid": True, "errors": []},
                    "schematron": {"valid": True, "errors": []},
                },
                indent=2,
            )
        )
    elif not quiet:
        typer.echo("-" * 60)
        typer.echo("VALIDATION SUCCESSFUL")


def _parse_asset_mapping(value: str) -> tuple[str, Path]:
    if "=" not in value:
        raise typer.BadParameter(f"Expected ARCHIVE_PATH=SOURCE, got {value!r}")
    archive_path, source = value.split("=", 1)
    if not archive_path or not source:
        raise typer.BadParameter(f"Expected ARCHIVE_PATH=SOURCE, got {value!r}")
    return archive_path, Path(source)


@app.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)
def pack(
    document: Path = typer.Argument(..., help="DocLang markup file (.dclg, .xml, …)", exists=True),
    output: Path | None = typer.Option(
        None,
        "-o",
        "--output",
        help="Output .dclx file (default: same stem as document, .dclx extension)",
    ),
    pages_dir: Path | None = typer.Option(
        None,
        "--pages",
        help="Directory of page images (1.png, 2.png, …)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    page_files: list[Path] | None = typer.Option(
        None,
        "--page",
        help="Page image; repeat to add pages in order (renumbered as 1.ext, 2.ext, …)",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    asset_mappings: list[str] | None = typer.Option(
        None,
        "--asset",
        help="Asset mapping ARCHIVE_PATH=SOURCE; repeat for multiple",
    ),
    assets_dir: Path | None = typer.Option(
        None,
        "--assets",
        help="Directory tree copied into assets/",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    validate_before_pack: bool = typer.Option(False, "--validate", help="Validate document before packing"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode (exit code only)"),
):
    """
    Pack a DocLang markup file and optional media into a .dclx archive.

    DOCUMENT is copied to document.xml. Optional page images (--pages, --page)
    are placed under pages/. Optional payload files (--assets, --asset) are
    placed under assets/ for URIs referenced in the markup. OPC metadata
    ([Content_Types].xml, _rels/.rels) is generated automatically.

    By default, writes <document>.dclx next to the input file.

    Examples:

        doclang pack markup.dclg
        doclang pack markup.dclg -o report.dclx --pages screenshots/
        doclang pack markup.dclg --page a.png --page b.png
        doclang pack markup.dclg --asset chart.svg=exports/diagram.svg
        doclang pack markup.dclg --assets payload/ --validate
    """
    if pages_dir is not None and page_files:
        typer.echo("Error: --pages and --page are mutually exclusive", err=True)
        raise typer.Exit(1)
    if assets_dir is not None and asset_mappings:
        typer.echo("Error: --assets and --asset are mutually exclusive", err=True)
        raise typer.Exit(1)

    output_path = output or document.with_suffix(".dclx")

    pages: Path | list[Path] | None
    if pages_dir is not None:
        pages = pages_dir
    elif page_files:
        pages = page_files
    else:
        pages = None

    assets: Path | dict[str, Path] | None
    if assets_dir is not None:
        assets = assets_dir
    elif asset_mappings:
        assets = dict(_parse_asset_mapping(value) for value in asset_mappings)
    else:
        assets = None

    try:
        created = pack_document(
            document,
            output=output_path,
            pages=pages,
            assets=assets,
            validate=validate_before_pack,
        )
    except ValidationError as exc:
        if not quiet:
            typer.echo(str(exc), err=True)
        raise typer.Exit(1)
    except PackagingError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    if not quiet:
        typer.echo(f"Created {created}")


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
    """DocLang toolkit."""


if __name__ == "__main__":
    app()
