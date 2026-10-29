"""Tests for migrating documents to another spec version."""

import sys
from pathlib import Path

import pytest

from doclang import MigrationError, SchematronBackendNotFound, UnsupportedVersionError, migrate
from doclang.migration._plan import NoMigrationPath, Step, _plan

VALID_DIR = Path(__file__).parent / "data" / "valid"
# <source>_to_<target>/ holds the cases, labelled by comments, in in.dclg or in several layouts (pretty.in.dclg,
# minified.in.dclg, hybrid.in.dclg), each with its expected result (out.dclg, pretty.out.dclg, ...)
CASES_DIR = Path(__file__).parent / "data" / "migration"

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
    assert result.xml.endswith("</doclang>\n")
    assert result.xml.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<doclang ')  # from <?xml version='1.0' ...


@pytest.mark.parametrize(
    ("start", "declared"),
    [(b"", False), (b"<?xml version='1.0'?>\n", True), (b'\xef\xbb\xbf<?xml version="1.0"?>\n', True)],
)
def test_xml_declaration_is_written_as_in_the_input(tmp_path, start, declared):
    doc = tmp_path / "doc.dclg"
    doc.write_bytes(start + f'<doclang xmlns="{NS}" version="0.8">\n  <text>x</text>\n</doclang>\n'.encode())
    xml = migrate(doc, to="0.7").xml
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>\n<doclang ' if declared else "<doclang ")
    assert xml.endswith("</doclang>\n")


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


@pytest.mark.parametrize("version", ["0.7", "0.8"])
def test_same_version_is_a_noop(tmp_path, version):
    body = "\n  <text>\n    x <bold>y</bold><content> z</content>\n  </text>\n"
    result = migrate(_doc(tmp_path, body, version=version), to=version)
    assert (result.source_version, result.changes) == (version, [])
    assert f'version="{version}">{body}</doclang>' in result.xml  # untouched, whitespace and <content> included


def test_newer_target_without_up_steps_only_updates_the_version(tmp_path):
    result = migrate(_doc(tmp_path, "\n  <text>x  <bold>y</bold> z</text>\n", version="0.7"), to="0.8")
    assert (result.source_version, result.target_version, result.changes) == ("0.7", "0.8", [])
    assert "<text>x  <bold>y</bold> z</text>" in result.xml and 'version="0.8"' in result.xml


def test_newer_target_from_a_version_without_schema_is_an_error(tmp_path):
    with pytest.raises(MigrationError, match=r"No schema for the document's version 0\.6"):
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


# --- up to the development head ------------------------------------------------------------------


def _with_unreleased_head(monkeypatch, apply):
    """As if the development schemas had unreleased changes, with ``apply`` as their up step."""
    from doclang.migration import _api

    monkeypatch.setattr(_api, "_head_description", lambda: "unreleased development version")
    monkeypatch.setattr(_api, "_load_steps", lambda newest, head: [Step(newest, head, apply)])


def test_up_steps_apply_on_the_way_to_the_head(tmp_path, monkeypatch):
    def mark(root, changes):
        root[0].text = "marked"

    _with_unreleased_head(monkeypatch, mark)
    result = migrate(_doc(tmp_path, "<text>x</text>"), to="0.9")
    assert (result.source_version, result.target_version) == ("0.8", "0.9")
    assert "<text>marked</text>" in result.xml and 'version="0.9"' in result.xml


def test_head_is_no_target_without_changes_of_its_own(tmp_path, monkeypatch):
    from doclang.migration import _api

    monkeypatch.setattr(_api, "_head_description", lambda: "0.8")  # as right after a release
    with pytest.raises(UnsupportedVersionError, match=r"No schema for DocLang spec version '0\.9'"):
        migrate(_doc(tmp_path, "<text>x</text>"), to="0.9")


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

    monkeypatch.setattr(_api, "_load_steps", lambda newest, head: [Step("0.8", "0.7", broken_step)])
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

    down = [Step("0.10", "0.9", noop), Step("0.9", "0.8", noop), Step("0.8", "0.7", noop)]
    up = [Step("0.7", "0.8", noop), Step("0.9", "0.10", noop)]  # none from 0.8 to 0.9
    return down + up


@pytest.mark.parametrize(
    ("source", "target", "expected"),
    [
        ("0.10", "0.9", [("0.10", "0.9")]),
        ("0.10", "0.7", [("0.10", "0.9"), ("0.9", "0.8"), ("0.8", "0.7")]),  # all the way down
        ("0.8", "0.8", []),
        ("0.7", "0.10", [("0.7", "0.8"), ("0.9", "0.10")]),  # 0.8 to 0.9 only updates the version
        ("0.8", "0.10", [("0.9", "0.10")]),
        ("0.8", "0.9", []),
    ],
)
def test_plan(source, target, expected):
    assert [(s.source, s.target) for s in _plan(source, target, _steps())] == expected


def test_plan_down_without_exact_path_fails():
    with pytest.raises(NoMigrationPath):
        _plan("0.8", "0.6", _steps())  # no step below 0.7


def test_newer_version_without_schema_is_migrated_down_as_the_latest(tmp_path):
    with pytest.warns(UserWarning, match=r"No schema for declared DocLang version 1\.0"):
        result = migrate(_doc(tmp_path, TRACK, version="1.0"), to="0.7")
    assert result.source_version == "1.0" and "track" not in result.xml


# --- every valid fixture ---------------------------------------------------------------------------


@pytest.mark.filterwarnings("ignore:No DocLang version declared")
@pytest.mark.parametrize("fixture", sorted(VALID_DIR.glob("*.dclg")), ids=lambda f: f.stem)
def test_every_valid_fixture_migrates_to_the_newest_released_version(fixture):
    """New head features must come with a migration rule: the result is validated against the old schema."""
    from doclang._schemas import _available_versions, _version_key

    newest = max(_available_versions(), key=_version_key)
    assert migrate(fixture, to=newest).target_version == newest


# --- file-based cases ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source", sorted(CASES_DIR.glob("*/*in.dclg")), ids=lambda f: f"{f.parent.name}/{f.name.removesuffix('.dclg')}"
)
def test_migration_case(source):
    """The cases migrate to the version their folder names and give the matching out.dclg exactly.

    Without it, one is written from the actual result, to review (and commit) before the test passes.
    """
    target = source.parent.name.split("_to_")[1]
    expected = source.with_name(source.name.removesuffix("in.dclg") + "out.dclg")
    actual = migrate(source, to=target).xml
    if not expected.exists():
        expected.write_text(actual, encoding="utf-8")
        pytest.fail(f"wrote {expected.name} from the actual result: review it, then rerun")
    assert actual == expected.read_text(encoding="utf-8")


# --- <content> in <field_heading> down to 0.8 ------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "downgraded", "kinds"),
    [
        (
            "<field_heading><italic>Contact:</italic><content>  </content>Address</field_heading>",
            "<field_heading><italic>Contact:<content>  </content></italic>Address</field_heading>",
            ["mapped"],
        ),
        (
            "<field_heading>Contact:<content>  </content> <italic>Address</italic></field_heading>",
            "<field_heading>Contact:<italic><content>  </content> Address</italic></field_heading>",
            ["mapped"],
        ),
        (
            "<field_heading>Contact:<content>  </content>Address</field_heading>",
            "<field_heading>Contact:  Address</field_heading>",
            ["dropped"],
        ),
    ],
)
def test_content_in_a_field_heading_goes_into_a_formatting_element(text, downgraded, kinds):
    """<field_heading> cannot hold <content>; it moves into a neighbouring formatting element, or is unwrapped."""
    from lxml import etree

    from doclang.migration._steps import from_next
    from doclang.migration._tree import Changes

    root, changes = etree.fromstring(f'<doclang xmlns="{NS}">{text}</doclang>'.encode()), Changes()
    from_next.migrate(root, changes)
    assert etree.tostring(root[0]).decode().replace(f' xmlns="{NS}"', "") == downgraded
    assert [c["kind"] for c in changes.items] == kinds
