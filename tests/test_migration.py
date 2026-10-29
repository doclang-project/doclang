"""Tests for migrating documents to another spec version."""

import sys
from pathlib import Path

import pytest

from doclang import MigrationError, SchematronBackendNotFound, UnsupportedVersionError, migrate
from doclang.migration._api import _head_version
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


def test_cdata_sections_are_written_as_in_the_input(tmp_path):
    result = migrate(_doc(tmp_path, f"<text>x <formula><![CDATA[p<0.001]]></formula></text>{TRACK}"), to="0.7")
    assert "<formula><![CDATA[p<0.001]]></formula>" in result.xml


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


@pytest.mark.parametrize("version", ["0.7", "0.8", "0.9"])
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


HEAD = _head_version("0.8")


def test_head_has_a_version_of_its_own():
    assert HEAD == "0.9"


def test_texts_are_stripped_and_unneeded_content_unwrapped(tmp_path):
    body = (
        "\n  <text>\n    Held on the 21\n    <superscript> st </superscript>\n"
        "    <content> of June, see </content>\n    <italic>the agenda</italic>\n.\n  </text>"
        "\n  <text>x <bold>y</bold> z</text>\n"
    )
    result = migrate(_doc(tmp_path, body), to=HEAD)

    assert (result.source_version, result.target_version, result.changes) == ("0.8", HEAD, [])
    assert (  # the target ignores the whitespace at the start and end of the body, so it stays
        "<text>\n    Held on the 21<superscript>st</superscript> of June, see <italic>the agenda</italic>.\n  </text>"
    ) in result.xml
    assert "<text>x<bold>y</bold>z</text>" in result.xml  # whitespace next to tags was not guaranteed
    assert f'<doclang xmlns="{NS}" version="{HEAD}">\n  <text>' in result.xml  # root layout is kept


def test_whitespace_the_target_ignores_is_kept(tmp_path):
    body = (
        "\n  <text>\n    "
        + "\n    ".join(f'<location value="{v}"/>' for v in (1, 2, 3, 4))
        + "\n    a\n    <bold>b</bold>\n  </text>"
        "\n  <list>\n    <ldiv/>\n    c\n    <ldiv/>\n    <italic>d</italic>\n  </list>"
        "\n  <field_region>\n    <field_item>\n      <key>e</key>\n    </field_item>\n  </field_region>\n"
    )
    result = migrate(_doc(tmp_path, body), to=HEAD)
    head = "\n    ".join(f'<location value="{v}"/>' for v in (1, 2, 3, 4))
    assert f"<text>\n    {head}\n    a<bold>b</bold>\n  </text>" in result.xml
    assert "<list>\n    <ldiv/>\n    c\n    <ldiv/>\n    <italic>d</italic>\n  </list>" in result.xml
    assert "<field_region>\n    <field_item>\n      <key>e</key>\n    </field_item>\n  </field_region>" in result.xml


def test_whitespace_between_paragraphs_of_a_list_item_is_kept(tmp_path):
    body = (
        "<list>\n  <ldiv/>\n  <text>First.</text>\n  <text>Second.</text>\n  <ldiv/>Fruit: <text>apples</text>\n</list>"
    )
    result = migrate(_doc(tmp_path, body), to=HEAD)
    assert "<ldiv/>\n  <text>First.</text>\n  <text>Second.</text>\n  <ldiv/>Fruit:<text>apples</text>" in result.xml


def test_content_comments_and_interior_whitespace_are_kept(tmp_path):
    body = "<code><content>\n  def f():\n      pass\n</content></code><text>a  b\n c<!-- note  --> d</text>"
    result = migrate(_doc(tmp_path, body), to=HEAD)
    assert "<content>\n  def f():\n      pass\n</content>" in result.xml
    assert "<text>a  b\n c<!-- note  -->d</text>" in result.xml  # interior whitespace reads as one space anyway


def test_cdata_sections_the_step_does_not_change_are_kept(tmp_path):
    result = migrate(_doc(tmp_path, "<text>x<formula><![CDATA[p<0.001]]></formula></text>"), to=HEAD)
    assert "<formula><![CDATA[p<0.001]]></formula>" in result.xml


def test_whitespace_other_than_space_tab_and_line_breaks_is_kept(tmp_path):
    result = migrate(_doc(tmp_path, "<text>\u00a0x\u2003</text>"), to=HEAD)
    assert "<text>\u00a0x\u2003</text>" in result.xml


def test_older_documents_get_the_head_steps_too(tmp_path):
    result = migrate(_doc(tmp_path, "<text>x <bold>y</bold></text>", version="0.7"), to=HEAD)
    assert "<text>x<bold>y</bold></text>" in result.xml and f'version="{HEAD}"' in result.xml


def test_head_documents_migrate_down_without_a_fallback_warning(tmp_path, recwarn):
    result = migrate(_doc(tmp_path, "<text>x</text>", version=HEAD), to="0.8")
    assert result.source_version == HEAD
    assert not [w for w in recwarn if "No schema" in str(w.message)]


def test_undeclared_version_to_the_head_only_gets_declared(tmp_path):
    with pytest.warns(UserWarning, match="No DocLang version declared"):
        result = migrate(_doc(tmp_path, "<text> x </text>", version=None), to=HEAD)
    assert "<text> x </text>" in result.xml and f'version="{HEAD}"' in result.xml


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


@pytest.mark.parametrize("fixture", sorted(VALID_DIR.glob("*.dclg")), ids=lambda f: f.stem)
def test_every_valid_fixture_migrates_from_the_newest_release_to_the_head(fixture, tmp_path):
    """The up steps keep documents valid: the result is validated against the development schemas."""
    from lxml import etree

    from doclang.validation import ValidationError, validate

    tree = etree.parse(str(fixture))
    tree.getroot().set("version", "0.8")
    doc = tmp_path / fixture.name
    tree.write(str(doc), encoding="UTF-8", xml_declaration=True)
    try:
        validate(doc, spec_version="0.8", allow_empty_namespace=True)
    except ValidationError:
        pytest.skip("uses what the newest release cannot express")
    assert migrate(doc, to=HEAD).target_version == HEAD


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


@pytest.mark.parametrize(
    "folder", [d for d in sorted(CASES_DIR.iterdir()) if len(list(d.glob("*.out.dclg"))) > 1], ids=lambda d: d.name
)
def test_layouts_migrate_alike(folder):
    """The layouts hold the same cases: their results have the same elements and read the same."""
    from lxml import etree

    def document(out: Path):
        root = etree.fromstring(out.read_bytes())
        return [(e.tag, dict(e.attrib)) for e in root.iter() if isinstance(e.tag, str)], _read(root)

    documents = [document(out) for out in sorted(folder.glob("*.out.dclg"))]
    assert all(d == documents[0] for d in documents)


# --- unwrapping <content> in the 0.8 to 0.9 step ---------------------------------------------------


def _read(root, rules: str = "0.9") -> list[str]:
    """What the whitespace rules read, one string per run of inline content in a body.

    Tags of inline elements are kept as markers (e.g. ``<bold>``), so that it shows which element a space belongs
    to. Written independently of the steps; only the element classification is shared. With the 0.8 rules, every
    text outside <content> is stripped and the pieces are joined directly; whitespace between words reads as one
    space, as with the 0.9 rules.
    """
    import re

    from doclang.migration._steps import to_next

    pieces: list[str] = []
    items: list[tuple[str, str]] = []  # (kind, text) with kind "ws", "word", "literal" or "tag"

    def add(text):
        if rules == "0.8":
            text = re.sub(r"[ \t\r\n]+", "\x00", (text or "").strip(" \t\r\n"))  # \x00: a space between words
            items.extend(("word", part.replace("\x00", " ")) for part in [text] if part)
            return
        for part in re.split(r"([ \t\r\n]+)", text or ""):
            if part:
                items.append(("ws" if not part.strip(" \t\r\n") else "word", part))

    def flush():
        content = [i for i, (kind, _) in enumerate(items) if kind in ("word", "literal")]
        if content:
            out, in_sequence = [], False
            for i, (kind, text) in enumerate(items):
                if kind == "ws":
                    if content[0] < i < content[-1] and not in_sequence:  # rule 2, then rules 3 and 4
                        out.append(" ")
                    in_sequence = True
                    continue
                if kind != "tag":
                    in_sequence = False  # a word, or <content>, whose whitespace is a sequence of its own
                out.append(text)
            pieces.append("".join(out))
        items.clear()

    def walk(element):
        add(element.text)
        for child in element:
            if to_next._inline(child):
                name = etree_localname(child)
                if name == "content":
                    items.append(("literal", child.text or ""))
                else:
                    items.append(("tag", f"<{name}>"))
                    walk(child)
                    items.append(("tag", f"</{name}>"))
            elif isinstance(child.tag, str) and etree_localname(child) in to_next._HEAD:
                apart(child)  # disregarded here, e.g. a caption is read on its own
            elif isinstance(child.tag, str) and etree_localname(child) in to_next._SEMANTIC:
                flush()  # e.g. one of two <text> paragraphs in a list item: a block of its own
                visit(child)
            elif isinstance(child.tag, str) and etree_localname(child) not in to_next._DELIMITERS:
                items.append(("literal", f"[{etree_localname(child)}]"))  # e.g. a checkbox: part of the text
                apart(child)
            elif not isinstance(child.tag, str):
                pass  # a comment or processing instruction: disregarded
            else:
                flush()  # a delimiter
                visit(child)
            add(child.tail)

    def apart(element):
        """Read the text blocks within ``element`` on their own."""
        outer = items[:]
        items.clear()
        visit(element)
        items[:] = outer

    def visit(element):
        name = etree_localname(element)
        if name in to_next._RAW_TEXT or name in to_next._VIRTUAL_TEXT:
            walk(element)
            flush()
        else:
            for child in element:
                if isinstance(child.tag, str):
                    visit(child)

    visit(root)
    return pieces


def etree_localname(element) -> str:
    from lxml import etree

    return etree.QName(element).localname


def _strip_only_and_full(xml: str):
    from lxml import etree

    from doclang.migration._steps import to_next
    from doclang.migration._tree import Changes

    stripped = etree.fromstring(xml.encode("utf-8"))
    to_next._strip_texts(stripped)
    full = etree.fromstring(xml.encode("utf-8"))
    to_next.migrate(full, Changes())
    return stripped, full


@pytest.mark.parametrize(
    "source",
    sorted((CASES_DIR / "0.8_to_0.9").glob("*in.dclg")) + sorted(VALID_DIR.glob("*.dclg")),
    ids=lambda f: f.stem,
)
def test_unwrapping_content_does_not_change_the_reading(source):
    stripped, full = _strip_only_and_full(source.read_text(encoding="utf-8"))
    assert _read(full) == _read(stripped)


@pytest.mark.parametrize(
    ("text", "unwrapped"),
    [
        ("<text>a<content> b</content></text>", "<text>a b</text>"),
        ("<text><content>a </content><bold>b</bold></text>", "<text>a <bold>b</bold></text>"),
        ("<text><bold><content>a </content></bold>b</text>", "<text><bold>a </bold>b</text>"),  # the space stays bold
        ("<list><ldiv/><content>a </content><italic>b</italic></list>", "<list><ldiv/>a <italic>b</italic></list>"),
        ("<text><content>a b</content></text>", "<text>a b</text>"),
    ],
)
def test_content_is_unwrapped_where_it_reads_the_same(text, unwrapped):
    from lxml import etree

    _, full = _strip_only_and_full(f'<doclang xmlns="{NS}">{text}</doclang>')
    assert etree.tostring(full[0]).decode().replace(f' xmlns="{NS}"', "") == unwrapped


@pytest.mark.parametrize(
    "text",
    [
        "<text>a<content>  b</content></text>",  # two spaces would collapse
        "<text>a<content>\nb</content></text>",  # a line break would read as a space
        "<text>a<content>\tb</content></text>",
        "<text><content> a</content></text>",  # at the start of the body, the space would be dropped
        "<text><content>a </content></text>",  # at its end, too
        '<text><location value="1"/><content> a</content></text>',  # after the element head, too
        "<text><bold><content> a</content></bold></text>",  # also within an inline element
        "<text>a<content> </content><content> </content>b</text>",  # adjacent spaces would merge
        "<list><ldiv/><content>a </content><ldiv/>b</list>",  # at the end of a list item
        "<text>a<!-- c --><content> b</content></text>",  # next to a comment
        "<code><content>def f():\n    pass</content></code>",
    ],
)
def test_content_stays_where_unwrapping_would_change_the_reading(text):
    _, full = _strip_only_and_full(f'<doclang xmlns="{NS}">{text}</doclang>')
    assert full.find(f".//{{{NS}}}content") is not None


def test_reader_reads_elements_without_raw_text_as_part_of_the_text():
    from lxml import etree

    xml = (
        f'<doclang xmlns="{NS}"><text>\n  <checkbox/> Accept the\n  <bold>terms</bold>, see\n'
        "  <picture><caption> Fig. 1 </caption></picture> below.\n</text></doclang>"
    )
    assert _read(etree.fromstring(xml)) == [
        "Fig. 1",  # the caption is a text block of its own
        "[checkbox] Accept the <bold>terms</bold>, see [picture] below.",
    ]


@pytest.mark.parametrize(
    ("text", "reading"),
    [
        (  # the head of a nested element is disregarded: one sequence across it
            '<text>Visit our <text><href uri="https://www.example.com"/>website</text> for more.</text>',
            ["Visit our <text>website</text> for more."],
        ),
        (  # the head of the text block itself, too
            '<text>\n  <location value="1"/><location value="2"/><location value="3"/><location value="4"/>\n  Hi</text>',
            ["Hi"],
        ),
        ("<text>c <!-- note --> d<?pi x?>e</text>", ["c de"]),  # comments and processing instructions, too
        (  # a caption is a text block of its own, with its own nested content
            "<picture><caption> Fig. <bold>1</bold> </caption></picture>",
            ["Fig. <bold>1</bold>"],
        ),
    ],
)
def test_reader_disregards_element_heads(text, reading):
    from lxml import etree

    assert _read(etree.fromstring(f'<doclang xmlns="{NS}">{text}</doclang>')) == reading


@pytest.mark.parametrize(
    ("text", "reading"),
    [
        (  # two paragraphs in a list item: blocks of their own
            "<list><ldiv/><text>Apples.</text> <text>Pears.</text></list>",
            ["Apples.", "Pears."],
        ),
        (  # with raw text, the item is a virtual <text> and the <text> is part of it
            "<list><ldiv/>Fruit: <text>apples</text></list>",
            ["Fruit: <text>apples</text>"],
        ),
        (  # the same for cells; formatting makes a cell a virtual <text> too
            "<table><fcel/><text>a</text> <text>b</text><fcel/><bold>x</bold> <text>y</text><nl/></table>",
            ["a", "b", "<bold>x</bold> <text>y</text>"],
        ),
    ],
)
def test_reader_reads_items_without_text_of_their_own_as_blocks(text, reading):
    from lxml import etree

    assert _read(etree.fromstring(f'<doclang xmlns="{NS}">{text}</doclang>')) == reading


def test_reader_reads_the_spec_example():
    from lxml import etree

    xml = (
        f'<doclang xmlns="{NS}"><text>\n  Water is H<subscript>2</subscript>O,\n  <bold>very </bold>\n'
        "  <italic> clear</italic> and <content>two  spaces</content> apart.\n</text></doclang>"
    )
    assert _read(etree.fromstring(xml)) == [
        "Water is H<subscript>2</subscript>O, <bold>very </bold><italic>clear</italic> and two  spaces apart."
    ]
