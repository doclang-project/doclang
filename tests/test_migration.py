"""Tests for migrating documents to another spec version."""

import sys
from pathlib import Path

import pytest

from doclang import MigrationError, SchematronBackendNotFound, UnsupportedVersionError, migrate
from doclang.migration._plan import NoMigrationPath, Step, _plan

VALID_DIR = Path(__file__).parent / "data" / "valid"

NS = "https://www.doclang.ai/ns/v0"
TRACK = '<track><bdiv/><minutes value="0"/><seconds value="2"/>Hello.</track>'


def _doc(tmp_path: Path, body: str, version: str | None = "0.8", namespace: bool = True) -> Path:
    attrs = (f' xmlns="{NS}"' if namespace else "") + (f' version="{version}"' if version is not None else "")
    path = tmp_path / "doc.dclg"
    path.write_text(f"<?xml version='1.0' encoding='UTF-8'?>\n<doclang{attrs}>{body}</doclang>", encoding="utf-8")
    return path


# --- rules ---------------------------------------------------------------------------------------


def test_track_is_dropped_with_its_surroundings_kept(tmp_path):
    doc = _doc(tmp_path, f"\n  <text>before</text>\n  {TRACK}\n  <text>after</text>\n")
    result = migrate(doc, to="0.7")

    assert "track" not in result.xml
    assert "<text>before</text>" in result.xml and "<text>after</text>" in result.xml
    assert [(c["kind"], c["location"]) for c in result.changes] == [("dropped", "/doclang/track")]
    assert result.changes[0]["line"] == 4
    assert (result.source_version, result.target_version) == ("0.8", "0.7")
    assert 'version="0.7"' in result.xml


def test_tracks_inside_group_and_table_cell_are_dropped(tmp_path):
    result = migrate(_doc(tmp_path, f"<group>{TRACK}</group><table><fcel/>{TRACK}<nl/></table>"), to="0.7")
    assert [c["location"] for c in result.changes] == ["/doclang/group/track", "/doclang/table/track"]


def test_multiple_captions_first_stays_others_become_text_after_parent(tmp_path):
    body = (
        "<picture><caption>FIG. 1</caption><caption>Source: A</caption><caption>Source: B</caption>"
        '<src uri="a.png"/></picture><text>next</text>'
    )
    result = migrate(_doc(tmp_path, body), to="0.7")

    assert result.xml.count("<caption>") == 1 and "<caption>FIG. 1</caption>" in result.xml
    assert "<text>Source: A</text><text>Source: B</text><text>next</text>" in result.xml
    assert [(c["kind"], c["location"]) for c in result.changes] == [
        ("mapped", "/doclang/picture/caption[2]"),
        ("mapped", "/doclang/picture/caption[3]"),
    ]


def test_single_caption_and_plain_documents_are_unchanged(tmp_path):
    result = migrate(_doc(tmp_path, "<picture><caption>FIG. 1</caption></picture><text>x</text>"), to="0.7")
    assert result.changes == []
    assert "<caption>FIG. 1</caption>" in result.xml


def test_document_without_namespace(tmp_path):
    doc = _doc(tmp_path, f"<text>x</text>{TRACK}", namespace=False)
    result = migrate(doc, to="0.7")
    assert "track" not in result.xml and len(result.changes) == 1


# --- strict --------------------------------------------------------------------------------------


def test_strict_fails_on_any_change_and_carries_them(tmp_path):
    with pytest.raises(MigrationError, match=r"would change 1 part") as excinfo:
        migrate(_doc(tmp_path, TRACK), to="0.7", strict=True)
    assert [c["kind"] for c in excinfo.value.changes] == ["dropped"]


def test_strict_passes_when_nothing_is_lost(tmp_path):
    result = migrate(_doc(tmp_path, "<text>x</text>"), to="0.7", strict=True)
    assert result.changes == []


# --- versions ------------------------------------------------------------------------------------


def test_same_version_is_a_noop(tmp_path):
    result = migrate(_doc(tmp_path, "<text>x</text>", version="0.7"), to="0.7")
    assert (result.source_version, result.changes) == ("0.7", [])


def test_newer_target_is_an_error(tmp_path):
    with pytest.raises(MigrationError, match="newer than the document's version"):
        migrate(_doc(tmp_path, "<text>x</text>", version="0.6"), to="0.7")


def test_target_without_schema_is_unsupported(tmp_path):
    with pytest.raises(UnsupportedVersionError, match=r"No schema for DocLang spec version '0\.1'"):
        migrate(_doc(tmp_path, "<text>x</text>"), to="0.1")


def test_malformed_declared_version(tmp_path):
    with pytest.raises(MigrationError, match="Invalid declared DocLang version 'v8'"):
        migrate(_doc(tmp_path, "<text>x</text>", version="v8"), to="0.7")


def test_undeclared_version_warns_is_treated_as_latest_and_gets_declared(tmp_path):
    with pytest.warns(UserWarning, match="No DocLang version declared"):
        result = migrate(_doc(tmp_path, TRACK, version=None), to="0.7")
    assert result.source_version is None
    assert 'version="0.7"' in result.xml and "track" not in result.xml


# --- validation of input and output ------------------------------------------------------------------

_UNKNOWN_ELEMENT = "<unknown_future_element/>"  # no schema knows it
_DANGLING_XREF = '<text><xref thread_id="1"/>x</text>'  # valid for the XSD, rejected by the Schematron rules


def test_invalid_input_is_rejected_before_migrating(tmp_path):
    with pytest.raises(MigrationError, match=r"The document is not valid for DocLang 0\.8; fix it before migrating"):
        migrate(_doc(tmp_path, _UNKNOWN_ELEMENT), to="0.7")


def test_invalid_input_that_was_not_validated_fails_on_output_with_a_hint(tmp_path):
    doc = _doc(tmp_path, _UNKNOWN_ELEMENT)
    with pytest.raises(MigrationError, match=r"bug in the migration steps, unless the input was already invalid"):
        migrate(doc, to="0.7", input_validation="none")
    assert migrate(doc, to="0.7", input_validation="none", output_validation="none").changes == []


def test_a_step_producing_an_invalid_document_is_reported_as_a_bug(tmp_path, monkeypatch):
    from lxml import etree

    from doclang.migration import _api

    def broken_step(root, changes):
        etree.SubElement(root, f"{{{NS}}}unknown_future_element")

    monkeypatch.setattr(_api, "_load_steps", lambda newest: {None: Step(None, "0.7", broken_step)})
    with pytest.raises(MigrationError) as excinfo:
        migrate(_doc(tmp_path, "<text>x</text>"), to="0.7")
    assert "bug in the migration steps:" in str(excinfo.value)  # no hint: the input was fully validated


@pytest.mark.parametrize(("scope", "valid"), [("all", False), ("xsd", True), ("schematron", False), ("none", True)])
def test_input_validation_scopes(tmp_path, scope, valid):
    doc = _doc(tmp_path, _DANGLING_XREF)
    if valid:
        assert migrate(doc, to="0.7", input_validation=scope, output_validation="none").changes == []
    else:
        with pytest.raises(MigrationError, match="fix it before migrating"):
            migrate(doc, to="0.7", input_validation=scope, output_validation="none")


@pytest.mark.parametrize(("scope", "ok"), [("all", False), ("xsd", True), ("schematron", False), ("none", True)])
def test_output_validation_scopes(tmp_path, scope, ok):
    doc = _doc(tmp_path, _DANGLING_XREF)
    if ok:
        assert migrate(doc, to="0.7", input_validation="none", output_validation=scope).changes == []
    else:
        with pytest.raises(MigrationError, match=r"not valid against DocLang 0\.7"):
            migrate(doc, to="0.7", input_validation="none", output_validation=scope)


def test_missing_schematron_backend_is_an_error_not_a_silent_downgrade(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "saxonche", None)  # as if not installed
    doc = _doc(tmp_path, "<text>x</text>")
    with pytest.raises(SchematronBackendNotFound):
        migrate(doc, to="0.7")
    with pytest.raises(SchematronBackendNotFound):
        migrate(doc, to="0.7", input_validation="xsd")  # the output is still validated in full
    assert migrate(doc, to="0.7", input_validation="xsd", output_validation="xsd").changes == []
    assert migrate(doc, to="0.7", input_validation="none", output_validation="none").changes == []


def test_unknown_validation_scope(tmp_path):
    with pytest.raises(ValueError, match=r"output_validation must be one of all, xsd, schematron, none; got 'xml'"):
        migrate(_doc(tmp_path, "<text>x</text>"), to="0.7", output_validation="xml")


# --- planning ------------------------------------------------------------------------------------


def _steps():
    def noop(root, changes):
        return None

    return {
        None: Step(None, "0.9", noop),
        "0.9": Step("0.9", "0.8", noop),
        "0.8": Step("0.8", "0.7", noop),
    }


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        (None, "0.9", [None]),  # head to the newest release
        (None, "0.7", [None, "0.9", "0.8"]),  # all the way down
        ("0.9", "0.7", ["0.9", "0.8"]),  # starts at a released version
        ("0.8", "0.8", []),
        ("1.0", "0.8", [None, "0.9"]),  # an unreleased version is treated as the head
    ],
)
def test_plan(source, target, expected):
    assert [s.source for s in _plan(source, target, _steps())] == expected


def test_plan_without_exact_path_fails():
    with pytest.raises(NoMigrationPath):
        _plan("0.8", "0.6", _steps())  # no step below 0.7


# --- every valid fixture ---------------------------------------------------------------------------


@pytest.mark.filterwarnings("ignore:No DocLang version declared")
@pytest.mark.parametrize("fixture", sorted(VALID_DIR.glob("*.dclg")), ids=lambda f: f.stem)
def test_every_valid_fixture_migrates_to_the_newest_released_version(fixture):
    """New head features must come with a migration rule: the result is validated against the old schema."""
    from doclang._schemas import _available_versions, _version_key

    newest = max(_available_versions(), key=_version_key)
    assert migrate(fixture, to=newest).target_version == newest
