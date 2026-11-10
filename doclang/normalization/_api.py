"""Implementation of the public normalization API (see ``doclang.normalization``)."""

from __future__ import annotations

import copy
import tempfile
from collections.abc import Collection
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Union

from lxml import etree

from doclang._packaging import PackagingError, _is_archive, _read_archive, _write_archive
from doclang.migration._api import _has_xml_declaration, _validate
from doclang.normalization._rules import RULE_IDS, RULES, Context
from doclang.utils import _parse_doclang_document
from doclang.validation import ValidationError

_VALIDATION_SCOPES = ("all", "xsd", "schematron", "none")


@dataclass(frozen=True)
class NormalizationResult:
    """The outcome of :func:`normalize`.

    ``changes`` lists what was rewritten, in the order the rules ran. Each change is a dict with the keys ``rule``
    (the rule id), ``tier`` (1 or 2), ``kind`` ("fixed"), ``location`` (path of the text block), ``line`` and
    ``message`` (e.g. ``CO₂ → <subscript>2</subscript>``). ``suggestions`` lists, in the same form with the kind
    "suggested", what the tier 2 rules would rewrite when they were not applied (``tier=1``).
    """

    xml: str
    changes: list[dict[str, Any]] = field(default_factory=list)
    suggestions: list[dict[str, Any]] = field(default_factory=list)


class NormalizationError(Exception):
    """Raised when a document cannot be normalized, e.g. because it or the result is invalid."""

    def __init__(self, message: str, *, changes: list[dict[str, Any]] | None = None) -> None:
        self.changes = changes or []
        super().__init__(message)


def rules() -> list[dict[str, Any]]:
    """The normalization rules in the order they run, each as ``{"id", "tier", "description"}``."""
    return [{"id": r.id, "tier": r.tier, "description": r.description} for r in RULES]


def normalize_tree(
    root: etree._Element, *, tier: int = 1, only: Collection[str] | None = None
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Normalize the document ``root`` in place; return the changes and the tier 2 suggestions (see
    :class:`NormalizationResult`)."""
    if tier not in (1, 2):
        raise ValueError(f"tier must be 1 or 2; got {tier!r}")
    unknown = sorted(set(only or ()) - set(RULE_IDS))
    if unknown:
        raise ValueError(f"unknown rule(s): {', '.join(unknown)}; known rules: {', '.join(RULE_IDS)}")
    selected = [r for r in RULES if only is None or r.id in only]

    changes = _run(root, [r for r in selected if r.tier <= tier])
    suggestions: list[dict[str, Any]] = []
    if tier == 1 and any(r.tier == 2 for r in selected):
        trial = copy.deepcopy(root)
        suggestions = [c for c in _run(trial, selected) if c["tier"] == 2]
    for change in changes:
        change["kind"] = "fixed"
    for change in suggestions:
        change["kind"] = "suggested"
    return changes, suggestions


def _run(root: etree._Element, selected: list[Any]) -> list[dict[str, Any]]:
    ctx = Context(root)
    for rule in selected:
        ctx.rule = rule
        rule.apply(ctx)
    return ctx.changes


def normalize(
    xml_file: Union[str, Path],
    *,
    tier: int = 1,
    rules: Collection[str] | None = None,
    output: Union[str, Path, None] = None,
    input_validation: str = "all",
    output_validation: str = "all",
) -> NormalizationResult:
    """Rewrite super/subscripts, symbols and inline math of a DocLang XML file or archive (``.dclx``) into the
    preferred representation of Annex C of the specification ("Representing scripts, symbols and math").

    ``tier`` selects the rules that are applied: 1 (default) applies the deterministic rules only, whose rewrites
    have one reading (e.g. ``℃`` → ``°C``, ``<formula>2x</formula><superscript>2</superscript>`` →
    ``<formula>2x^{2}</formula>``); what the heuristic tier 2 rules would rewrite is reported in ``suggestions``.
    2 also applies the tier 2 rules (e.g. ``x<superscript>2</superscript>`` → ``<formula>x^{2}</formula>``), which
    read the surrounding text and can be wrong. ``rules`` limits the run to the rules with these ids (see
    :func:`rules`).

    The normalized document is returned in the result and, if ``output`` is given, written there: as a file for an
    XML file, as an archive for an archive (whose other members are copied as they are). The document keeps its
    version.

    The document is validated before and the result after normalizing; ``input_validation`` and
    ``output_validation`` select what runs ("all", "xsd", "schematron" or "none"), as for
    :func:`~doclang.migrate`. An invalid input raises :class:`NormalizationError`, and so does an invalid result,
    which indicates a bug in a rule.
    """
    for label, scope in (("input_validation", input_validation), ("output_validation", output_validation)):
        if scope not in _VALIDATION_SCOPES:
            raise ValueError(f"{label} must be one of {', '.join(_VALIDATION_SCOPES)}; got {scope!r}")

    path = Path(xml_file)
    if not _is_archive(path):
        result = _normalize(path, tier, rules, input_validation, output_validation)
        if output is not None:
            Path(output).write_text(result.xml, encoding="utf-8")
        return result

    try:
        _, document = _read_archive(path)
    except PackagingError as exc:
        raise NormalizationError(str(exc)) from exc
    with tempfile.TemporaryDirectory() as tmp:
        document_path = Path(tmp) / "document.xml"
        document_path.write_bytes(document)
        result = _normalize(document_path, tier, rules, input_validation, output_validation)
    if output is not None:
        _write_archive(path, output, result.xml.encode("utf-8"), {})
    return result


def _normalize(
    path: Path,
    tier: int,
    only: Collection[str] | None,
    input_validation: str,
    output_validation: str,
) -> NormalizationResult:
    tree = _parse_doclang_document(path, keep_cdata=True)
    root = tree.getroot()
    has_namespace = etree.QName(root).namespace is not None

    def input_failure(exc: ValidationError) -> NormalizationError:
        return NormalizationError(f"The document is not valid; fix it before normalizing:\n{exc}")

    _validate(path, input_validation, allow_empty_namespace=not has_namespace, failure=input_failure)

    changes, suggestions = normalize_tree(root, tier=tier, only=only)

    xml = etree.tostring(tree, encoding="UTF-8", xml_declaration=False).decode("utf-8") + "\n"
    if _has_xml_declaration(path):
        xml = f'<?xml version="1.0" encoding="UTF-8"?>\n{xml}'

    def output_failure(exc: ValidationError) -> NormalizationError:
        return NormalizationError(
            f"The normalized document is not valid; this is a bug in a normalization rule:\n{exc}", changes=changes
        )

    with tempfile.TemporaryDirectory() as tmp:
        normalized = Path(tmp) / "normalized.dclg"
        normalized.write_text(xml, encoding="utf-8")
        _validate(normalized, output_validation, allow_empty_namespace=not has_namespace, failure=output_failure)

    return NormalizationResult(xml=xml, changes=changes, suggestions=suggestions)


for _public in (NormalizationResult, NormalizationError, normalize, rules):
    _public.__module__ = "doclang.normalization"
