"""Implementation of the public migration API (see ``doclang.migration``)."""

from __future__ import annotations

import re
import tempfile
import warnings
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

from lxml import etree

from doclang._packaging import PackagingError, _is_archive, _read_archive, _write_archive
from doclang._schemas import UnsupportedVersionError, _available_versions, _head_description, _version_key
from doclang.migration import _archive
from doclang.migration._plan import NoMigrationPath, _load_steps, _plan
from doclang.migration._tree import Changes
from doclang.utils import _parse_doclang_document
from doclang.validation import ValidationError, validate

_VERSION_RE = re.compile(r"^\d+\.\d+$")
_VALIDATION_SCOPES = ("all", "xsd", "schematron", "none")


@dataclass(frozen=True)
class MigrationResult:
    """The outcome of :func:`migrate`.

    ``changes`` lists what was mapped or dropped, in document order. Each change is a dict with the keys
    ``kind`` ("mapped" or "dropped"), ``location`` (path of the element), ``line`` and ``message``. For an
    archive, the members renamed, removed or orphaned by dropped elements follow, with the ``kind`` "renamed",
    "removed" or "orphaned", the member name as ``location`` and ``line`` None. The ``kind`` values are stable; ``message``
    is meant for humans.
    """

    xml: str
    source_version: str | None  # None if the document declared no version and no source was given
    target_version: str
    changes: list[dict[str, Any]] = field(default_factory=list)


class MigrationError(Exception):
    """Raised when a document cannot be migrated as requested.

    ``changes`` holds what the migration would have changed, if it got that far.
    """

    def __init__(self, message: str, *, changes: list[dict[str, Any]] | None = None) -> None:
        self.changes = changes or []
        super().__init__(message)


def migrate(
    xml_file: Union[str, Path],
    *,
    to: str,
    source: str | None = None,
    output: Union[str, Path, None] = None,
    strict: bool = False,
    input_validation: str = "all",
    output_validation: str = "all",
) -> MigrationResult:
    """Migrate a DocLang XML file or archive (``.dclx``) to the spec version ``to`` (``MAJOR.MINOR``).

    The migrated document is returned in the result and, if ``output`` is given, written there: as a file for
    an XML file, as an archive for an archive. An archive is migrated by migrating its ``document.xml``; all
    other members are copied as they are, except for the whole-track media when ``<track>`` elements are
    dropped: that of the remaining tracks is renumbered to stay aligned with them, and that of the dropped ones
    removed, as it would pair with another track. Members that only dropped elements used and that can stay
    (files under ``assets/`` that only they referenced, the media of dropped tracks if none remain) are kept and
    reported as orphaned; they do not count as changes for ``strict``.

    The source version is the ``version`` attribute of the root element. If it is missing, the document is
    treated as the latest version and a :class:`UserWarning` is issued, unless ``source`` gives its version.
    ``source`` (``MAJOR.MINOR``, a version with bundled schemas or the development head) is meant for such
    undeclared documents; for a document that declares a different version, :class:`MigrationError` is raised.

    ``to`` can be an older or a newer version with bundled schemas, or, while the development schemas have
    unreleased changes, the next minor version after the newest released one (validated against the development
    schemas). Migrating to a newer version rewrites the document where the newer version reads the same markup
    differently, so that it keeps its meaning; otherwise only the version changes, as documents are forward
    compatible. A document whose version has no bundled schemas cannot be migrated up.

    By default the migration is best effort: content that has an equivalent in the target version is mapped,
    the rest is dropped, and every such change is reported in ``changes``. With ``strict=True`` any change
    raises :class:`MigrationError` instead.

    The document is validated before the migration (against its own version) and the result afterwards (against
    the target version). ``input_validation`` and ``output_validation`` select what runs: "all" (XSD and
    Schematron), "xsd", "schematron" or "none". As with :func:`~doclang.validate`, Schematron needs a backend
    and :class:`SchematronBackendNotFound` is raised if there is none. An invalid input raises
    :class:`MigrationError`. A failing output indicates a bug in a migration step (or an invalid input that was
    not validated) and also raises :class:`MigrationError`.

    Raises :class:`UnsupportedVersionError` if there is no schema for ``to`` or ``source``, and :class:`ValueError` for an
    unknown validation scope. An archive that cannot be read (e.g. without ``document.xml``) raises
    :class:`MigrationError`.
    """
    for name, scope in (("input_validation", input_validation), ("output_validation", output_validation)):
        if scope not in _VALIDATION_SCOPES:
            raise ValueError(f"{name} must be one of {', '.join(_VALIDATION_SCOPES)}; got {scope!r}")
    options: dict[str, Any] = {
        "to": to,
        "source": source,
        "strict": strict,
        "input_validation": input_validation,
        "output_validation": output_validation,
    }

    path = Path(xml_file)
    if not _is_archive(path):
        result, _ = _migrate(path, None, **options)
        if output is not None:
            Path(output).write_text(result.xml, encoding="utf-8")
        return result

    try:
        members, document = _read_archive(path)
    except PackagingError as exc:
        raise MigrationError(str(exc)) from exc
    with tempfile.TemporaryDirectory() as tmp:
        document_path = Path(tmp) / "document.xml"
        document_path.write_bytes(document)
        result, renames = _migrate(document_path, [m.filename for m in members], **options)
    if output is not None:
        _write_archive(path, output, result.xml.encode("utf-8"), renames)
    return result


def _migrate(
    path: Path,
    members: Sequence[str] | None,
    *,
    to: str,
    source: str | None,
    strict: bool,
    input_validation: str,
    output_validation: str,
) -> tuple[MigrationResult, dict[str, str | None]]:
    """Migrate the XML file ``path`` (see :func:`migrate`), with the renames of the archive ``members`` (or
    of none, if it is no archive's)."""
    available = _available_versions()
    newest = max(available, key=_version_key) if available else None
    head = _head_version(newest)
    targets = available + ([head] if head else [])
    for version in (to, source):
        if version is not None and version not in targets:
            raise UnsupportedVersionError(
                f"No schema for DocLang spec version '{version}'; available versions: {', '.join(targets) or 'none'}"
            )

    tree = _parse_doclang_document(path, keep_cdata=True)  # written back as in the input
    root = tree.getroot()
    has_namespace = etree.QName(root).namespace is not None

    declared = root.get("version")
    if source is not None and declared is not None and declared != source:
        raise MigrationError(f"The document declares version {declared}, not the given source version {source}")
    if declared is None:
        declared = source  # from here on: the version the document is read as
    if declared is None:
        warnings.warn(
            "No DocLang version declared; migrating from the latest version.",
            UserWarning,
            stacklevel=3,
        )
    elif not _VERSION_RE.match(declared):
        raise MigrationError(f"Invalid declared DocLang version '{declared}'; expected MAJOR.MINOR")
    upward = declared is not None and _version_key(declared) < _version_key(to)
    if upward and declared not in targets:
        raise MigrationError(f"No schema for the document's version {declared}; cannot migrate it to {to}")

    _validate(
        path,
        input_validation,
        allow_empty_namespace=not has_namespace,
        failure=_input_failure(declared),
        spec_version=source if source != head else None,  # the head is the default without a declared version
        head=declared is not None and declared == head,
    )

    changes = Changes()
    assert newest is not None  # ``to`` is one of the available versions or the next one
    start = declared if declared in targets else head or newest  # no version or a newer one: the latest
    try:
        steps = _plan(start, to, _load_steps(newest, head))
    except NoMigrationPath as exc:
        raise MigrationError(str(exc)) from exc
    tracks, assets = _archive.tracks(root), _archive.asset_references(root)
    for step in steps:
        step.apply(root, changes)
    renames = {} if members is None else _archive.member_renames(members, tracks, assets, root, changes)

    changed = [c for c in changes.items if c["kind"] != "orphaned"]
    if strict and changed:
        raise MigrationError(
            f"Migrating to {to} would change {len(changed)} part(s) of the document; "
            "pass strict=False to accept the changes",
            changes=changes.items,
        )

    root.set("version", to)
    xml = etree.tostring(tree, encoding="UTF-8", xml_declaration=False).decode("utf-8") + "\n"
    if _has_xml_declaration(path):  # written here: lxml would use single quotes
        xml = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml}'

    _validate_output(xml, to, output_validation, input_validation, has_namespace, changes.items, head=to == head)

    return MigrationResult(xml=xml, source_version=declared, target_version=to, changes=changes.items), renames


def _has_xml_declaration(path: Path) -> bool:
    """Whether the document starts with an XML declaration (after an optional byte order mark)."""
    with path.open("rb") as f:
        start = f.read(16)
    for bom, encoding in ((b"\xef\xbb\xbf", "utf-8"), (b"\xff\xfe", "utf-16-le"), (b"\xfe\xff", "utf-16-be")):
        if start.startswith(bom):
            return start[len(bom) :].startswith("<?xml".encode(encoding))
    return start.startswith(b"<?xml")


def _head_version(newest: str | None) -> str | None:
    """The version of the development head: the minor after the newest released one, or None if the head has
    no changes of its own (as any change to the spec makes a new minor version)."""
    if newest is None or _head_description() == newest:
        return None
    major, minor = _version_key(newest)
    return f"{major}.{minor + 1}"


def _validate(
    path: Path,
    scope: str,
    *,
    allow_empty_namespace: bool,
    failure: Callable[[ValidationError], MigrationError],
    spec_version: str | None = None,
    head: bool = False,
) -> None:
    """Validate ``path`` as :func:`~doclang.validation.validate` does, limited to ``scope``.

    With ``head``, the document declares the version of the development head and is validated against it.
    """
    if scope == "none":
        return
    try:
        with warnings.catch_warnings():
            # migrate() already warns about a missing version
            warnings.filterwarnings("ignore", message="No DocLang version declared")
            if head:  # intended: the head's version has no bundled schemas yet
                warnings.filterwarnings("ignore", message="No schema for declared DocLang version")
            validate(
                path,
                spec_version=spec_version,
                allow_empty_namespace=allow_empty_namespace,
                xsd_only=scope == "xsd",
                schematron_only=scope == "schematron",
            )
    except ValidationError as exc:
        raise failure(exc) from exc


def _input_failure(declared: str | None) -> Callable[[ValidationError], MigrationError]:
    label = f"DocLang {declared}" if declared else "the latest DocLang version"
    return lambda exc: MigrationError(f"The document is not valid for {label}; fix it before migrating:\n{exc}")


def _validate_output(
    xml: str,
    to: str,
    scope: str,
    input_scope: str,
    has_namespace: bool,
    changes: list[dict[str, Any]],
    *,
    head: bool,
) -> None:
    unless = "" if input_scope == "all" else f", unless the input was already invalid (input validation: {input_scope})"

    def failure(exc: ValidationError) -> MigrationError:
        return MigrationError(
            f"The migrated document is not valid against DocLang {to}; this is a bug in the migration steps{unless}:\n{exc}",
            changes=changes,
        )

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "migrated.dclg"
        path.write_text(xml, encoding="utf-8")
        _validate(
            path,
            scope,
            allow_empty_namespace=not has_namespace,
            spec_version=None if head else to,
            failure=failure,
            head=head,
        )


# present the public names as living in ``doclang.migration`` (in reprs, error messages, pickles)
for _public in (MigrationResult, MigrationError, migrate):
    _public.__module__ = "doclang.migration"
