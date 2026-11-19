"""
DocLang CLI - Command-line interface for the DocLang toolkit.

Provides a user-friendly CLI using Typer for working with DocLang documents.
"""

import json
import warnings
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import typer

from doclang._packaging import _archive_rules_apply, _archive_rules_version, _document_file, _is_archive
from doclang._schemas import UnsupportedVersionError, _select_schemas
from doclang.migration import MigrationError
from doclang.migration import migrate as migrate_document
from doclang.packaging import PackagingError
from doclang.packaging import pack as pack_document
from doclang.schematron import SchematronBackendNotFound
from doclang.utils import _VERSION
from doclang.validation import ValidationError, VersionNote
from doclang.validation import validate as validate_document

app = typer.Typer(
    name="doclang",
    help="DocLang toolkit",
    add_completion=False,
    no_args_is_help=True,
)


class ValidationScope(str, Enum):
    """What part of the validation to run."""

    all = "all"
    xsd = "xsd"
    schematron = "schematron"
    none = "none"


class OutputFormat(str, Enum):
    """Output format options."""

    text = "text"
    json = "json"


@app.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)
def validate(
    ctx: typer.Context,
    xml_file: Path = typer.Argument(..., help="XML file or .dclx archive to validate", exists=True),
    xsd_only: bool = typer.Option(False, "--xsd-only", help="Validate XSD only"),
    schematron_only: bool = typer.Option(False, "--schematron-only", help="Validate Schematron only"),
    allow_empty_namespace: bool = typer.Option(
        False,
        "--allow-empty-namespace",
        "-n",
        help="Allow documents without namespace (auto-inject DocLang namespace)",
    ),
    spec_version: Optional[str] = typer.Option(
        None,
        "--spec-version",
        help="DocLang spec version (MAJOR.MINOR) to validate against, overriding the document's version",
    ),
    strict_xsd_version_attr: bool = typer.Option(
        False,
        "--strict-xsd-version-attr",
        help=(
            "Apply the XSD's own check of the root `version` attribute as is. By default, if the XSD only accepts "
            "its own version (0.7) and the document declares another, the declared version is replaced in memory "
            "for XSD validation. Has no effect for XSDs that accept any MAJOR.MINOR, or with --schematron-only."
        ),
    ),
    strict_declared_version: bool = typer.Option(
        False,
        "--strict-declared-version",
        help=(
            "Fail if no schema is bundled for the document's declared version. By default the latest schema "
            "is used instead, with a warning."
        ),
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode (exit code only)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose output"),
    format: OutputFormat = typer.Option(OutputFormat.text, "--format", "-f", help="Output format"),
):
    """
    Validate XML document against bundled XSD schema and Schematron rules.

    For a .dclx archive, its document.xml is validated, and (unless --xsd-only
    or --schematron-only) its other parts are checked against the archive rules
    (Annex B, from version 0.8): the OPC metadata, the original source and its
    descriptor, page images and whole-track media beyond the pages and <track>
    elements of the document, and <src> URIs that resolve to no part. Parts
    that nothing accounts for are warned about.

    Examples:

        doclang validate document.xml
        doclang validate document.dclx
        doclang validate document.xml --xsd-only
        doclang validate document.xml --spec-version 0.7
        doclang validate document.xml --spec-version 0.7 --strict-xsd-version-attr
        doclang validate document.xml --format json
    """
    try:
        document = ctx.with_resource(_document_file(xml_file))
    except PackagingError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    try:
        selection = _select_schemas(document, spec_version, strict_declared_version=strict_declared_version)
    except UnsupportedVersionError as exc:
        # An unsupported declared version is reported as a validation failure below.
        if spec_version is not None:
            typer.echo(f"Error: {exc}", err=True)
            raise typer.Exit(1)
        selection = None
    except FileNotFoundError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    check_archive = (
        _is_archive(xml_file)
        and not xsd_only
        and not schematron_only
        and _archive_rules_apply(_archive_rules_version(document, spec_version))
    )
    bundled_xsd = selection.xsd if selection else None
    bundled_sch = selection.sch if selection else None

    if not quiet and format == OutputFormat.text:
        typer.echo(f"Validating: {xml_file}")
        typer.echo("-" * 60)

    notes: list[str] = []
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                validate_document(
                    xml_file,
                    allow_empty_namespace=allow_empty_namespace,
                    xsd_only=xsd_only,
                    schematron_only=schematron_only,
                    spec_version=spec_version,
                    strict_xsd_version_attr=strict_xsd_version_attr,
                    strict_declared_version=strict_declared_version,
                )
            finally:
                for w in caught:
                    notes.append(str(w.message))
                    if not quiet:
                        label = "Note" if issubclass(w.category, VersionNote) else "Warning"
                        typer.echo(f"{label}: {w.message}", err=True)
    except SchematronBackendNotFound as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    except ValidationError as exc:
        results: dict[str, Any] = {
            "xsd": {"valid": not exc.xsd_errors, "errors": exc.xsd_errors},
            "schematron": {"valid": not exc.schematron_errors, "errors": exc.schematron_errors},
        }
        if check_archive:
            results["archive"] = {"valid": not exc.archive_errors, "errors": exc.archive_errors}
        results["notes"] = notes

        if not quiet and format == OutputFormat.text:
            if not schematron_only:
                if verbose:
                    typer.echo("XSD Validation")
                    typer.echo(f"Schema: {bundled_xsd or 'n/a'}")
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
                    typer.echo(f"Schema: {bundled_sch or 'n/a'}")
                _echo_located_errors("Schematron", exc.schematron_errors)

            if check_archive:
                _echo_located_errors("Archive", exc.archive_errors)

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
                typer.echo(f"Schema: {bundled_xsd or 'n/a'}")
            typer.echo("XSD validation passed")

        if not xsd_only:
            if verbose:
                typer.echo("Schematron Validation")
                typer.echo(f"Schema: {bundled_sch or 'n/a'}")
            typer.echo("Schematron validation passed")

        if check_archive:
            typer.echo("Archive validation passed")

    if format == OutputFormat.json:
        sections = ["xsd", "schematron", "archive"] if check_archive else ["xsd", "schematron"]
        typer.echo(
            json.dumps(
                {**{section: {"valid": True, "errors": []} for section in sections}, "notes": notes},
                indent=2,
            )
        )
    elif not quiet:
        typer.echo("-" * 60)
        typer.echo("VALIDATION SUCCESSFUL")


def _echo_located_errors(kind: str, errors: list[dict[str, Any]]) -> None:
    if not errors:
        typer.echo(f"{kind} validation passed")
        return
    typer.echo(f"{kind} validation failed")
    for error in errors:
        typer.echo(f"  {error['location']}")
        typer.echo(f"    {error['message']}")


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
    audio_dir: Path | None = typer.Option(
        None,
        "--audio-dir",
        help="Directory of whole-track audio files (2.mp3, 4.ogg, …)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    audio_files: list[Path] | None = typer.Option(
        None,
        "--audio",
        help="Whole-track audio file; repeat to add tracks in order (renumbered as 1.ext, 2.ext, …)",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    video_dir: Path | None = typer.Option(
        None,
        "--video-dir",
        help="Directory of whole-track video files (3.mp4, 4.mkv, …)",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    video_files: list[Path] | None = typer.Option(
        None,
        "--video",
        help="Whole-track video file; repeat to add tracks in order (renumbered as 1.ext, 2.ext, …)",
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    source_file: Path | None = typer.Option(
        None,
        "--source",
        help=(
            "Original source document, stored unchanged as source.<ext> (or source without an extension), "
            "unless it is already packed, e.g. as --audio"
        ),
        exists=True,
        file_okay=True,
        dir_okay=False,
    ),
    source_mimetype: str | None = typer.Option(
        None,
        "--source-mimetype",
        help="MIME type of the original source, e.g. application/pdf (needed if its extension has no known type)",
    ),
    source_name: str | None = typer.Option(
        None,
        "--source-name",
        help="Original file name of the source, recorded in a source descriptor (source-metadata.xml)",
    ),
    keep_source_name: bool = typer.Option(
        False,
        "--keep-source-name",
        help="Record the --source file's own name as its original file name (instead of --source-name)",
    ),
    validate_before_pack: bool = typer.Option(False, "--validate", help="Validate document before packing"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Quiet mode (exit code only)"),
):
    """
    Pack a DocLang markup file and optional media into a .dclx archive.

    DOCUMENT is copied to document.xml. Optional page images (--pages, --page)
    are placed under pages/. Optional whole-track audio/video (--audio-dir,
    --audio, --video-dir, --video) are placed under audio/ and video/ as
    {N}.{ext} for the Nth <track>. Optional payload files (--assets, --asset)
    are placed under assets/ for URIs referenced in the markup. An optional
    original source document (--source) is stored unchanged as source.<ext>
    (unless it is already packed, e.g. as --audio, which is then reused) and
    located through a package relationship; --keep-source-name also records
    its file name, or --source-name another original file name. OPC metadata ([Content_Types].xml, _rels/.rels) is
    generated automatically.

    By default, writes <document>.dclx next to the input file.

    Examples:

        doclang pack markup.dclg
        doclang pack markup.dclg -o report.dclx --pages screenshots/
        doclang pack markup.dclg --page a.png --page b.png
        doclang pack markup.dclg --asset chart.svg=exports/diagram.svg
        doclang pack markup.dclg --audio-dir recordings/ --video-dir recordings/
        doclang pack markup.dclg --assets payload/ --validate
        doclang pack markup.dclg --source report.pdf --source-name "Q3 report.pdf"
        doclang pack markup.dclg --audio episode-12.mp3 --source episode-12.mp3 --keep-source-name
    """
    if pages_dir is not None and page_files:
        typer.echo("Error: --pages and --page are mutually exclusive", err=True)
        raise typer.Exit(1)
    if assets_dir is not None and asset_mappings:
        typer.echo("Error: --assets and --asset are mutually exclusive", err=True)
        raise typer.Exit(1)
    if audio_dir is not None and audio_files:
        typer.echo("Error: --audio-dir and --audio are mutually exclusive", err=True)
        raise typer.Exit(1)
    if video_dir is not None and video_files:
        typer.echo("Error: --video-dir and --video are mutually exclusive", err=True)
        raise typer.Exit(1)
    if keep_source_name and source_name is not None:
        typer.echo("Error: --keep-source-name and --source-name are mutually exclusive", err=True)
        raise typer.Exit(1)
    if keep_source_name:
        if source_file is None:
            typer.echo("Error: --keep-source-name needs --source", err=True)
            raise typer.Exit(1)
        source_name = source_file.name

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

    audio: Path | list[Path] | None = audio_dir if audio_dir is not None else (audio_files or None)
    video: Path | list[Path] | None = video_dir if video_dir is not None else (video_files or None)

    try:
        created = pack_document(
            document,
            output=output_path,
            pages=pages,
            assets=assets,
            audio=audio,
            video=video,
            source=source_file,
            source_mimetype=source_mimetype,
            source_name=source_name,
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


@app.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    no_args_is_help=True,
)
def migrate(
    document: Path = typer.Argument(..., help="DocLang markup file (.dclg, .xml, …) or .dclx archive", exists=True),
    to: str = typer.Option(..., "--to", help="Spec version (MAJOR.MINOR) to migrate the document to"),
    source: str | None = typer.Option(
        None,
        "--from",
        help="Spec version (MAJOR.MINOR) of a document that declares none (default: the latest version)",
    ),
    output: Path | None = typer.Option(
        None,
        "-o",
        "--output",
        help="Write the migrated document (or archive) here (default: stdout; required for an archive)",
    ),
    strict: bool = typer.Option(
        False,
        "--strict",
        help="Fail if anything would be mapped or dropped (default: best effort, reporting what changed)",
    ),
    input_validation: ValidationScope = typer.Option(
        ValidationScope.all,
        "--input-validation",
        help="Validation of the document before migrating, against its own version",
    ),
    output_validation: ValidationScope = typer.Option(
        ValidationScope.all,
        "--output-validation",
        help="Validation of the migrated document against the target version",
    ),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Do not report changes and warnings"),
    format: OutputFormat = typer.Option(OutputFormat.text, "--format", "-f", help="Output format"),
):
    """
    Migrate a DocLang document to a specific spec version.

    The migrated document goes to stdout (or --output); changes and warnings go to stderr. With
    --format json, stdout holds a JSON object with the versions, the changes and the document.

    A .dclx archive is migrated to another archive (--output): its document.xml is migrated, the
    other files are copied, except the media of dropped tracks if tracks remain, which is removed
    while that of the remaining tracks is renumbered. Other files only dropped elements used are
    kept and reported as orphaned.

    Examples:

        doclang migrate document.dclg --to 0.7
        doclang migrate document.dclg --to 0.7 -o document_0.7.dclg
        doclang migrate document.dclg --to 0.7 --strict --format json
        doclang migrate undeclared.dclg --from 0.8 --to 0.9
        doclang migrate document.dclx --to 0.7 -o document_0.7.dclx
    """
    if output is None and _is_archive(document):
        typer.echo("Error: an archive cannot be written to stdout; pass --output (-o)", err=True)
        raise typer.Exit(1)
    warning_messages: list[str] = []
    try:
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always")
            try:
                result = migrate_document(
                    document,
                    to=to,
                    source=source,
                    output=output,
                    strict=strict,
                    input_validation=input_validation.value,
                    output_validation=output_validation.value,
                )
            finally:
                warning_messages = [str(w.message) for w in caught]
    except (MigrationError, UnsupportedVersionError, SchematronBackendNotFound) as exc:
        changes = exc.changes if isinstance(exc, MigrationError) else []
        if format == OutputFormat.json:
            typer.echo(json.dumps({"error": str(exc), "changes": changes, "notes": warning_messages}, indent=2))
        elif not quiet:
            for message in warning_messages:
                typer.echo(f"Warning: {message}", err=True)
            typer.echo(f"Error: {exc}", err=True)
            for change in changes:
                typer.echo(_format_change(change), err=True)
        else:
            typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)
    except (OSError, ValueError) as exc:  # unreadable, malformed or DTD-bearing input
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    if format == OutputFormat.json:
        payload: dict[str, Any] = {
            "source_version": result.source_version,
            "target_version": result.target_version,
            "changes": result.changes,
            "notes": warning_messages,
        }
        if output is None:
            payload["xml"] = result.xml
        typer.echo(json.dumps(payload, indent=2))
        return

    if output is None:
        typer.echo(result.xml, nl=False)  # ends with a newline already
    if not quiet:
        for message in warning_messages:
            typer.echo(f"Warning: {message}", err=True)
        for change in result.changes:
            typer.echo(_format_change(change), err=True)
        if output is not None:
            typer.echo(f"Migrated to {result.target_version}: {output}", err=True)


def _format_change(change: dict[str, Any]) -> str:
    line = "" if change["line"] is None else f" (line {change['line']})"
    return f"  {change['kind'].capitalize()}: {change['location']}{line}: {change['message']}"


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
