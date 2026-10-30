"""Implementation of the public migration API (see ``doclang.migration``)."""

from __future__ import annotations

import re
import tempfile
import warnings
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

from lxml import etree

from doclang._schemas import UnsupportedVersionError, _available_versions, _head_description, _version_key
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
    ``kind`` ("mapped" or "dropped"), ``location`` (path of the element), ``line`` and ``message``. The
    ``kind`` values are stable; ``message`` is meant for humans.
    """

    xml: str
    source_version: str | None  # None if the document declared no version
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
    strict: bool = False,
    input_validation: str = "all",
    output_validation: str = "all",
) -> MigrationResult:
    """Migrate a DocLang XML file to the spec version ``to`` (``MAJOR.MINOR``).

    The source version is the ``version`` attribute of the root element. If it is missing, the document is
    treated as the latest version and a :class:`UserWarning` is issued.

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

    Raises :class:`UnsupportedVersionError` if there is no schema for ``to``, and :class:`ValueError` for an
    unknown validation scope.
    """
    for name, scope in (("input_validation", input_validation), ("output_validation", output_validation)):
        if scope not in _VALIDATION_SCOPES:
            raise ValueError(f"{name} must be one of {', '.join(_VALIDATION_SCOPES)}; got {scope!r}")

    available = _available_versions()
    newest = max(available, key=_version_key) if available else None
    head = _head_version(newest)
    targets = available + ([head] if head else [])
    if to not in targets:
        raise UnsupportedVersionError(
            f"No schema for DocLang spec version '{to}'; available versions: {', '.join(targets) or 'none'}"
        )

    path = Path(xml_file)
    tree = _parse_doclang_document(path, keep_cdata=True)  # written back as in the input
    root = tree.getroot()
    has_namespace = etree.QName(root).namespace is not None

    declared = root.get("version")
    if declared is None:
        warnings.warn(
            "No DocLang version declared; migrating from the latest version.",
            UserWarning,
            stacklevel=2,
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
        head=declared is not None and declared == head,
    )

    changes = Changes()
    assert newest is not None  # ``to`` is one of the available versions or the next one
    source = declared if declared in targets else head or newest  # no version or a newer one: the latest
    try:
        steps = _plan(source, to, _load_steps(newest, head))
    except NoMigrationPath as exc:
        raise MigrationError(str(exc)) from exc
    for step in steps:
        step.apply(root, changes)

    if strict and changes.items:
        raise MigrationError(
            f"Migrating to {to} would change {len(changes.items)} part(s) of the document; "
            "pass strict=False to accept the changes",
            changes=changes.items,
        )

    root.set("version", to)
    xml = etree.tostring(tree, encoding="UTF-8", xml_declaration=False).decode("utf-8") + "\n"
    if _has_xml_declaration(path):  # written here: lxml would use single quotes
        xml = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml}'

    _validate_output(xml, to, output_validation, input_validation, has_namespace, changes.items, head=to == head)

    return MigrationResult(xml=xml, source_version=declared, target_version=to, changes=changes.items)


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
