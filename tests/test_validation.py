"""
Pytest test suite for DocLang XML schema validation.

Tests both valid and invalid XML documents against XSD and Schematron rules
via the public ``validate()`` API.
"""

import builtins
import re
import sys
import warnings
import zipfile
from collections.abc import Mapping
from pathlib import Path
from unittest.mock import patch

import pytest

import doclang
from doclang import (
    SchematronBackendNotFound,
    SchematronViolation,
    UnsupportedVersionError,
    ValidationError,
    validate,
)
from doclang._schemas import _available_versions
from doclang.utils import _DTD_REJECTED_MESSAGE, _write_xml_without_dtd
from doclang.validation import VersionNote

TEST_DATA_DIR = Path(__file__).parent / "data"
VALID_DIR = TEST_DATA_DIR / "valid"
INVALID_DIR = TEST_DATA_DIR / "invalid"
SCHEMA_DIR = Path(doclang.__file__).resolve().parent


# Collect test files
valid_files = list(VALID_DIR.glob("*.dclg")) if VALID_DIR.exists() else []
invalid_files = list(INVALID_DIR.glob("*.dclg")) if INVALID_DIR.exists() else []


def _allow_empty_namespace(xml_file: Path) -> bool:
    return xml_file.stem in ["ok_no_namespace", "doclang_example"]


@pytest.mark.parametrize("xml_file", valid_files, ids=lambda f: f.stem)
def test_valid(xml_file):
    """Test that valid XML files pass both XSD and Schematron validation."""
    assert validate(xml_file, allow_empty_namespace=_allow_empty_namespace(xml_file)) is None


@pytest.mark.parametrize("xml_file", invalid_files, ids=lambda f: f.stem)
def test_invalid(xml_file):
    """Test that invalid XML files fail validation."""
    with pytest.raises(ValidationError) as exc_info:
        validate(xml_file, allow_empty_namespace=False)

    exc = exc_info.value
    assert exc.xsd_errors or exc.schematron_errors, f"Expected {xml_file.name} to fail validation, but it passed"

    if exc.xsd_errors:
        assert len(exc.xsd_errors) > 0, f"Expected XSD validation errors for {xml_file.name}"
    if exc.schematron_errors:
        assert len(exc.schematron_errors) > 0, f"Expected Schematron validation errors for {xml_file.name}"


def test_invalid_reports_both_xsd_and_schematron_errors():
    """A document may fail both XSD and Schematron validation in a single run."""
    xml_file = INVALID_DIR / "nok_xsd_and_schematron.dclg"
    with pytest.raises(ValidationError) as exc_info:
        validate(xml_file, allow_empty_namespace=False)

    exc = exc_info.value
    assert len(exc.xsd_errors) == 1
    assert len(exc.schematron_errors) == 1


def test_dtd_and_entity_payloads_are_rejected(tmp_path: Path):
    """DTD / entity payloads are rejected with a clear error (no expansion)."""
    bomb = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE doclang [
  <!ENTITY a "aaaaaaaaaa">
  <!ENTITY b "&a;&a;&a;&a;&a;&a;&a;&a;&a;&a;">
  <!ENTITY c "&b;&b;&b;&b;&b;&b;&b;&b;&b;&b;">
  <!ENTITY d "&c;&c;&c;&c;&c;&c;&c;&c;&c;&c;">
  <!ENTITY e "&d;&d;&d;&d;&d;&d;&d;&d;&d;&d;">
]>
<doclang xmlns="https://www.doclang.ai/ns/v0" version="0.7">
  <text>&e;</text>
</doclang>
"""
    xml_file = tmp_path / "entity_bomb.dclg"
    xml_file.write_text(bomb, encoding="utf-8")

    with pytest.raises(ValidationError) as exc_info:
        validate(xml_file, xsd_only=True)

    assert any(_DTD_REJECTED_MESSAGE in (err.get("error") or "") for err in exc_info.value.xsd_errors)


def test_doctype_without_entities_is_rejected(tmp_path: Path):
    """A DOCTYPE alone is enough to reject — DocLang does not use DTDs."""
    xml_file = tmp_path / "with_doctype.dclg"
    xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE doclang>
<doclang xmlns="https://www.doclang.ai/ns/v0" version="0.7">
  <text>Hello</text>
</doclang>
""",
        encoding="utf-8",
    )

    with pytest.raises(ValidationError) as exc_info:
        validate(xml_file, xsd_only=True)

    assert any(_DTD_REJECTED_MESSAGE in (err.get("error") or "") for err in exc_info.value.xsd_errors)


def test_schematron_temp_serialization_omits_doctype(tmp_path: Path):
    """Saxon input must not re-emit a DOCTYPE even if parse somehow retained one."""
    # Build a tree via the safe parser without going through the reject helper,
    # then ensure the Schematron rewrite path strips DOCTYPE.
    from doclang.utils import _parse_xml

    xml_file = tmp_path / "doctype.dclg"
    xml_file.write_text(
        """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE doclang [
  <!ENTITY x "secret">
]>
<doclang xmlns="https://www.doclang.ai/ns/v0" version="0.7">
  <text>&x;</text>
</doclang>
""",
        encoding="utf-8",
    )
    doc = _parse_xml(xml_file)
    assert (doc.docinfo.doctype or "").strip()

    out = tmp_path / "rewritten.xml"
    with out.open("wb") as handle:
        _write_xml_without_dtd(doc, handle)

    rewritten = out.read_text(encoding="utf-8")
    assert "<!DOCTYPE" not in rewritten
    assert "<!ENTITY" not in rewritten


def test_schema_files_exist():
    """Test that required schema files are bundled with the package."""
    assert (SCHEMA_DIR / "doclang.xsd").exists(), f"XSD file not found under {SCHEMA_DIR}"
    assert (SCHEMA_DIR / "doclang.sch").exists(), f"Schematron file not found under {SCHEMA_DIR}"


def test_test_directories_exist():
    """Test that test directories exist and contain files."""
    assert VALID_DIR.exists(), f"Valid test directory not found: {VALID_DIR}"
    assert INVALID_DIR.exists(), f"Invalid test directory not found: {INVALID_DIR}"
    assert len(valid_files) > 0, "No valid test files found"
    assert len(invalid_files) > 0, "No invalid test files found"


class _AlwaysFailingSchematronValidator:
    def validate(self, xml_path: Path, *, schema_path: Path, allow_empty_namespace: bool = False):
        return [SchematronViolation(location="/doclang", message="custom backend failure")]


def test_custom_schematron_validator():
    """A caller-provided Schematron backend is used instead of the default."""
    xml_file = valid_files[0]
    with pytest.raises(ValidationError) as exc_info:
        validate(xml_file, schematron=_AlwaysFailingSchematronValidator())

    assert exc_info.value.schematron_errors == [{"location": "/doclang", "message": "custom backend failure"}]


def test_schematron_backend_not_found():
    """Missing default backend raises SchematronBackendNotFound."""
    xml_file = valid_files[0]
    with patch("doclang.validation._default_schematron_validator", side_effect=SchematronBackendNotFound):
        with pytest.raises(SchematronBackendNotFound):
            validate(xml_file, schematron_only=True)


def test_schematron_backend_not_found_when_saxonche_missing():
    """Missing saxonche extra raises SchematronBackendNotFound, not ValidationError."""
    xml_file = valid_files[0]
    real_import = builtins.__import__
    saxonche_modules = [name for name in sys.modules if name == "saxonche" or name.startswith("saxonche.")]

    def import_without_saxonche(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "saxonche" or name.startswith("saxonche."):
            raise ModuleNotFoundError("No module named 'saxonche'")
        return real_import(name, globals, locals, fromlist, level)

    with (
        patch.dict(sys.modules, dict.fromkeys(saxonche_modules)),
        patch("builtins.__import__", side_effect=import_without_saxonche),
    ):
        with pytest.raises(SchematronBackendNotFound):
            validate(xml_file, schematron_only=True)


# --- spec version selection ---------------------------------------------------

VALID_DOC = (VALID_DIR / "ok_namespaced_and_versioned.dclg").read_text(encoding="utf-8")


def _doc(tmp_path: Path, version: str | None) -> Path:
    attr = f' version="{version}"' if version is not None else ""
    path = tmp_path / "doc.dclg"
    path.write_text(f'<doclang xmlns="https://www.doclang.ai/ns/v0"{attr}><text>hi</text></doclang>', encoding="utf-8")
    return path


@pytest.fixture
def schema_dir(tmp_path, monkeypatch):
    """A package-like schema dir: released schemas at 0.7, 1.0 and 1.2, and a development head labeled 1.3."""
    import shutil

    from doclang import _schemas

    root = tmp_path / "pkg"
    root.mkdir()
    xsd = (SCHEMA_DIR / "doclang.xsd").read_text(encoding="utf-8")
    current = _schemas._current_version()
    for name in ("0.7", "1.0", "1.2"):
        folder = root / "schemas" / name
        folder.mkdir(parents=True)
        (folder / "doclang.xsd").write_text(xsd.replace(f'version="{current}.', f'version="{name}.'), encoding="utf-8")
        shutil.copy(SCHEMA_DIR / "doclang.sch", folder / "doclang.sch")
    (root / "doclang.xsd").write_text(xsd.replace(f'version="{current}.', 'version="1.3.'), encoding="utf-8")
    shutil.copy(SCHEMA_DIR / "doclang.sch", root / "doclang.sch")
    monkeypatch.setattr(_schemas, "_SCHEMA_DIR", root)
    return root


def test_select_schemas_precedence(schema_dir, tmp_path):
    from doclang._schemas import _select_schemas

    assert _select_schemas(_doc(tmp_path, "0.7")).version == "0.7"
    assert _select_schemas(_doc(tmp_path, "0.7"), "1.2").version == "1.2"  # explicit override wins
    unversioned = _select_schemas(_doc(tmp_path, None))
    assert (unversioned.version, unversioned.declared, unversioned.xsd) == ("1.3", False, schema_dir / "doclang.xsd")


def test_select_schemas_major_one_falls_back_to_newer_minor(schema_dir, tmp_path):
    from doclang._schemas import _select_schemas

    assert _select_schemas(_doc(tmp_path, "1.1")).version == "1.2"  # 1.1 instance, nearest newer schemas 1.2


def test_select_schemas_declared_without_schemas_falls_back_to_head(schema_dir, tmp_path):
    from doclang._schemas import UnsupportedVersionError, _select_schemas

    for declared in ("1.4", "0.8", "0.1"):  # newer than any schemas; within 0.x no compatibility fallback; older
        selection = _select_schemas(_doc(tmp_path, declared))
        assert (selection.xsd, selection.head_fallback_for) == (schema_dir / "doclang.xsd", declared)
    with pytest.raises(UnsupportedVersionError, match=r"No schema for declared DocLang version '0\.8'"):
        _select_schemas(_doc(tmp_path, "0.8"), strict_declared_version=True)


def test_validate_unversioned_warns():
    path = VALID_DIR / "ok_no_namespace.dclg"
    with pytest.warns(UserWarning, match="No DocLang version declared"):
        validate(path, allow_empty_namespace=True)


def test_validate_explicit_spec_version(schema_dir, tmp_path):
    validate(_doc(tmp_path, "1.2"), xsd_only=True, spec_version="1.2")
    with pytest.raises(UnsupportedVersionError, match=r"No schema for DocLang spec version '9\.9'; available versions"):
        validate(_doc(tmp_path, "1.2"), xsd_only=True, spec_version="9.9")
    with pytest.raises(UnsupportedVersionError):
        validate(_doc(tmp_path, "1.2"), xsd_only=True, spec_version="1.3")  # head only, no released schemas


def test_validate_declared_version_without_schemas_warns_and_uses_head(tmp_path):
    with pytest.warns(UserWarning, match=r"No schema for declared DocLang version 0\.1; validating against the latest"):
        assert validate(_doc(tmp_path, "0.1"), xsd_only=True) is None


def test_strict_declared_version_fails_without_schemas(tmp_path):
    with pytest.raises(ValidationError, match=r"No schema for declared DocLang version '0\.1'"):
        validate(_doc(tmp_path, "0.1"), xsd_only=True, strict_declared_version=True)


def test_strict_declared_version_allows_versions_with_schemas(tmp_path):
    assert validate(_doc(tmp_path, "0.7"), xsd_only=True, strict_declared_version=True) is None


def test_08_document_validates_against_the_released_08_schema(tmp_path):
    import warnings

    track_08 = _versioned_doc(tmp_path, "0.8", _TRACK_BODY)
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # a released version needs no fallback, so no warning
        assert validate(track_08) is None
        assert validate(track_08, strict_declared_version=True) is None
        assert validate(track_08, spec_version="0.8") is None


def test_newer_declared_version_falls_back_to_the_head(tmp_path):
    """The fallback message names the head by its version if it is identical to that released schema, else as
    unreleased."""
    newest = max(_available_versions(), key=lambda v: tuple(map(int, v.split("."))))
    major, minor = map(int, newest.split("."))
    newer = f"{major}.{minor + 1}"
    doc = _versioned_doc(tmp_path, newer, _TRACK_BODY)
    head = rf"({re.escape(newest)}|unreleased development version)"
    with pytest.warns(
        UserWarning, match=rf"No schema for declared DocLang version {re.escape(newer)}; .*latest schema \({head}\)\."
    ):
        assert validate(doc) is None
    with pytest.raises(ValidationError, match=rf"No schema for declared DocLang version '{re.escape(newer)}'"):
        validate(doc, strict_declared_version=True)


def test_version_attribute_only_constrained_to_format(tmp_path):
    """The XSD does not tie the declared version to the schema: a 0.8-declared doc validates as 0.7."""
    with pytest.warns(UserWarning):
        assert validate(_doc(tmp_path, "0.8"), xsd_only=True, spec_version="0.7") is None
        with pytest.raises(ValidationError):
            validate(_doc(tmp_path, "v1"), xsd_only=True, spec_version="0.7")  # not MAJOR.MINOR


def test_validate_notes_override_differing_from_declared(tmp_path):
    with pytest.warns(UserWarning, match="declares version 0.8; validating as 0.7"):
        with pytest.warns(VersionNote):
            validate(_doc(tmp_path, "0.8"), xsd_only=True, spec_version="0.7")


def test_declared_version_normalized_for_schemas_with_version_enumeration(schema_dir, tmp_path):
    """Older schemas restrict `version` to their own value; a differing declared version is not an error."""
    folder = schema_dir / "schemas" / "0.6"
    folder.mkdir(parents=True)
    xsd = (schema_dir / "doclang.xsd").read_text(encoding="utf-8")
    xsd = xsd.replace('version="1.3.', 'version="0.6.').replace(
        '<xs:pattern value="[0-9]+\\.[0-9]+"/>', '<xs:enumeration value="0.6"/>'
    )
    (folder / "doclang.xsd").write_text(xsd, encoding="utf-8")
    (folder / "doclang.sch").write_text((schema_dir / "doclang.sch").read_text(encoding="utf-8"), encoding="utf-8")

    with pytest.warns(UserWarning, match="declares version 1.2; validating as 0.6"):
        with pytest.warns(VersionNote):
            assert validate(_doc(tmp_path, "1.2"), xsd_only=True, spec_version="0.6") is None


def test_bundled_07_schemas_are_the_released_ones():
    """schemas/0.7 is the unmodified v0.7.3 snapshot: it knows nothing of later constructs like <track>."""
    assert "0.7" in _available_versions()
    xsd = (SCHEMA_DIR / "schemas" / "0.7" / "doclang.xsd").read_text(encoding="utf-8")
    assert 'name="track"' not in xsd


def test_track_document_fails_as_07_and_passes_against_head():
    track_doc = VALID_DIR / "ok_track_minimal.dclg"
    with pytest.raises(ValidationError):
        validate(track_doc, spec_version="0.7")
    with pytest.warns(UserWarning, match="No DocLang version declared"):
        assert validate(track_doc) is None  # unspecified: development head


def test_enumerated_versions_only_for_released_07_schema():
    from doclang._schemas import _enumerated_versions

    assert _enumerated_versions(SCHEMA_DIR / "schemas" / "0.7" / "doclang.xsd") == {"0.7"}
    assert _enumerated_versions(SCHEMA_DIR / "doclang.xsd") == set()  # head: format only


def test_declared_version_not_rewritten_for_format_only_schemas(schema_dir, tmp_path):
    """Targets that don't pin `version` get the document as is, and no 'not checked' remark."""
    from unittest.mock import patch as mock_patch

    from doclang import xsd_validation

    with (
        mock_patch.object(xsd_validation, "_validate_xsd_at", wraps=xsd_validation._validate_xsd_at) as spy,
        pytest.warns(UserWarning, match=r"declares version 1\.0; validating as 1\.2 as requested\.$"),
    ):
        validate(_doc(tmp_path, "1.0"), xsd_only=True, spec_version="1.2")
    assert spy.call_args.kwargs["schema_version"] is None


def test_rewrite_is_explained_by_separate_note_when_enumerating_schema_used(tmp_path):
    with pytest.warns(UserWarning) as record:
        validate(_doc(tmp_path, "0.8"), xsd_only=True, spec_version="0.7")
    plain = [str(w.message) for w in record if not issubclass(w.category, VersionNote)]
    notes = [str(w.message) for w in record if issubclass(w.category, VersionNote)]
    assert plain == ["Document declares version 0.8; validating as 0.7 as requested."]
    assert len(notes) == 1
    assert 'replaced with "0.7" in memory' in notes[0]
    assert "not modified" in notes[0]
    assert "--strict-xsd-version-attr" in notes[0]


def test_strict_xsd_version_attr_applies_xsd_check_as_is(tmp_path):
    with pytest.warns(UserWarning, match="declares version 0.8; validating as 0.7 as requested") as record:
        with pytest.raises(ValidationError, match="version"):
            validate(_doc(tmp_path, "0.8"), xsd_only=True, spec_version="0.7", strict_xsd_version_attr=True)
    assert not any(issubclass(w.category, VersionNote) for w in record)  # nothing was rewritten


def test_strict_xsd_version_attr_has_no_effect_for_format_only_schemas(schema_dir, tmp_path):
    with pytest.warns(UserWarning, match="declares version 1.0; validating as 1.2 as requested"):
        validate(_doc(tmp_path, "1.0"), xsd_only=True, spec_version="1.2", strict_xsd_version_attr=True)


# --- validating against 0.7: one scenario matrix, same content throughout --------------------------


def _versioned_doc(tmp_path: Path, version: str, body: str = "<text>hi</text>") -> Path:
    path = tmp_path / f"doc_{version}.dclg"
    path.write_text(
        f'<doclang xmlns="https://www.doclang.ai/ns/v0" version="{version}">{body}</doclang>', encoding="utf-8"
    )
    return path


_TRACK_BODY = '<track><bdiv/><minutes value="0"/><seconds value="2"/>Hello.</track>'


def test_07_document_against_07_passes_without_warning(tmp_path):
    import warnings

    doc = _versioned_doc(tmp_path, "0.7")
    with warnings.catch_warnings():
        warnings.simplefilter("error")  # any warning fails the test
        assert validate(doc, spec_version="0.7") is None
        assert validate(doc) is None  # declared version alone selects 0.7


def test_08_document_with_07_content_against_07_passes_with_warning(tmp_path):
    doc = _versioned_doc(tmp_path, "0.8")
    with pytest.warns(UserWarning) as record:
        assert validate(doc, spec_version="0.7") is None
    messages = [str(w.message) for w in record]
    assert any("declares version 0.8; validating as 0.7 as requested" in m for m in messages)
    assert any(issubclass(w.category, VersionNote) for w in record)


def test_08_document_with_07_content_against_07_fails_when_strict(tmp_path):
    doc = _versioned_doc(tmp_path, "0.8")
    with pytest.warns(UserWarning, match="declares version 0.8; validating as 0.7 as requested"):
        with pytest.raises(ValidationError) as excinfo:
            validate(doc, spec_version="0.7", strict_xsd_version_attr=True)
    assert "version" in str(excinfo.value)
    assert "track" not in str(excinfo.value)  # fails on the version attribute only


@pytest.mark.parametrize("strict", [False, True])
def test_08_document_with_track_against_07_fails_on_content(tmp_path, strict):
    doc = _versioned_doc(tmp_path, "0.8", _TRACK_BODY)
    with pytest.warns(UserWarning):
        with pytest.raises(ValidationError) as excinfo:
            validate(doc, spec_version="0.7", strict_xsd_version_attr=strict)
    assert "track" in str(excinfo.value)


def test_head_described_by_label_only_when_identical_to_released_schema(schema_dir):
    import shutil

    from doclang._schemas import _head_description

    # fixture head is labeled 1.3 and has no released 1.3 schemas
    assert _head_description() == "unreleased development version"

    folder = schema_dir / "schemas" / "1.3"
    folder.mkdir()
    for name in ("doclang.xsd", "doclang.sch"):
        shutil.copy(schema_dir / name, folder / name)
    assert _head_description() == "1.3"  # identical: the label is reliable

    (folder / "doclang.sch").write_text((folder / "doclang.sch").read_text(encoding="utf-8") + "\n<!-- changed -->")
    assert _head_description() == "unreleased development version"


def test_fallback_warnings_describe_the_head(schema_dir, tmp_path):
    with pytest.warns(UserWarning, match=r"latest schema \(unreleased development version\)\.$"):
        validate(_doc(tmp_path, None), xsd_only=True)
    with pytest.warns(
        UserWarning, match=r"No schema for declared DocLang version 1\.4; .*\(unreleased development version\)"
    ):
        validate(_doc(tmp_path, "1.4"), xsd_only=True)


_LOC = '<location value="10"/><location value="20"/><location value="30"/><location value="40"/>'


@pytest.mark.parametrize(
    "body",
    [
        # non-first branches of union rule contexts
        f'<heading level="1">stray{_LOC}</heading>',
        f"<table><ecel/>stray{_LOC}<nl/></table>",
        f"<index><fcel/>stray{_LOC}<nl/></index>",
        f'<list class="unordered">stray{_LOC}<ldiv/>item</list>',
        # text equal in value to the head must not be mistaken for it
        '<list class="unordered"><ldiv/>stray<caption>stray</caption></list>',
        "<table><fcel/>stray<caption>stray</caption><nl/></table>",
    ],
    ids=["heading", "table_ecel", "index_fcel", "list_own_head", "list_same_value", "table_same_value"],
)
def test_text_before_element_head_is_rejected(tmp_path, body):
    path = tmp_path / "doc.dclg"
    path.write_text(f'<doclang xmlns="https://www.doclang.ai/ns/v0">{body}</doclang>', encoding="utf-8")
    with pytest.raises(ValidationError) as excinfo:
        validate(path)
    assert not excinfo.value.xsd_errors
    assert any("before element head" in str(e) for e in excinfo.value.schematron_errors)


# --- archives --------------------------------------------------------------------------------------

_CONTENT_TYPES = (
    '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
    '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
    '<Default Extension="png" ContentType="image/png"/><Default Extension="mp3" ContentType="audio/mpeg"/>'
    '<Default Extension="ogg" ContentType="audio/ogg"/>'
    '<Override PartName="/document.xml" ContentType="application/vnd.doclang.document+xml"/></Types>'
)


def _rels(*relationships: tuple[str, str]) -> str:
    """``_rels/.rels`` with the document relationship and ``relationships`` (type suffix, target; an ``http:``
    target is external)."""
    elements = "".join(
        f'<Relationship Id="rId{n}" Type="http://doclang.ai/ns/package/2026/relationships/{kind}" Target="{target}"'
        + (' TargetMode="External"' if target.startswith("http:") else "")
        + "/>"
        for n, (kind, target) in enumerate([("document", "document.xml"), *relationships], start=1)
    )
    return f'<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">{elements}</Relationships>'


_RELS = _rels()
# Two pages and one <track>.
_DOCUMENT = (
    '<doclang xmlns="https://www.doclang.ai/ns/v0" version="0.9">'
    '<text>One.</text><page_break/><track><bdiv/><seconds value="1"/>Hi.</track></doclang>'
)


def _archive(tmp_path: Path, members: Mapping[str, bytes | str | None], *, document: str = _DOCUMENT) -> Path:
    """An archive of ``document`` (by default two pages and one ``<track>``) with valid OPC metadata, unless
    ``members`` replaces it or (with None) leaves it out."""
    path = tmp_path / "doc.dclx"
    base = {"[Content_Types].xml": _CONTENT_TYPES, "_rels/.rels": _RELS, "document.xml": document}
    with zipfile.ZipFile(path, "w") as archive:
        for name, data in {**base, **members}.items():
            if data is not None:
                archive.writestr(name, data)
    return path


def _archive_errors(path: Path, **options) -> list[tuple[str, str]]:
    try:
        validate(path, **options)
    except ValidationError as exc:
        assert not exc.xsd_errors and not exc.schematron_errors
        assert "Archive validation failed" in str(exc)
        return [(e["location"], e["message"]) for e in exc.archive_errors]
    return []


def test_valid_archive(tmp_path: Path):
    members = {"pages/1.png": b"", "pages/2.png": b"", "audio/1.mp3": b"", "assets/a.png": b""}
    assert _archive_errors(_archive(tmp_path, members)) == []


@pytest.mark.parametrize(
    ("members", "location", "message"),
    [
        ({"[Content_Types].xml": None}, "[Content_Types].xml", "Missing"),
        ({"[Content_Types].xml": "<Types"}, "[Content_Types].xml", "Not well-formed XML"),
        (
            {"[Content_Types].xml": _CONTENT_TYPES.replace("document+xml", "other+xml")},
            "[Content_Types].xml",
            "No <Override> for /document.xml",
        ),
        ({"assets/data.json": b"{}"}, "assets/data.json", "No content type"),
        ({"source": b"%PDF"}, "source", "No content type"),
        ({"_rels/.rels": None}, "_rels/.rels", "Missing"),
        (
            {"_rels/.rels": _RELS.replace('Target="document.xml"', 'Target="other.xml"')},
            "_rels/.rels",
            "must target document.xml",
        ),
        ({"_rels/.rels": _RELS.replace("/document", "/other")}, "_rels/.rels", "found 0"),
        ({"pages/3.png": b""}, "pages/3.png", "the document has 2 page(s)"),
        ({"audio/2.mp3": b""}, "audio/2.mp3", "the document has 1 <track>(s)"),
        ({"audio/1.mp3": b"", "audio/1.ogg": b""}, "audio/1.ogg", "More than one audio file for <track> 1"),
    ],
)
def test_invalid_archive(tmp_path: Path, members, location, message):
    errors = _archive_errors(_archive(tmp_path, members))
    assert [e[0] for e in errors] == [location]
    assert message in errors[0][1]


def test_archive_rules_are_skipped_before_0_8_and_for_partial_validation(tmp_path: Path):
    """0.7 has no archive format (e.g. a migration to 0.7 keeps the media of the removed tracks)."""
    document = '<doclang xmlns="https://www.doclang.ai/ns/v0" version="0.7"><text>Hi.</text></doclang>'
    archive = _archive(tmp_path, {"audio/1.mp3": b"", "[Content_Types].xml": None}, document=document)
    assert _archive_errors(archive) == []

    archive = _archive(tmp_path, {"audio/2.mp3": b""})
    assert _archive_errors(archive, xsd_only=True) == []
    assert _archive_errors(archive, schematron_only=True) == []


def test_archive_errors_come_with_document_errors(tmp_path: Path):
    document = '<doclang xmlns="https://www.doclang.ai/ns/v0" version="0.9"><unknown/></doclang>'
    path = _archive(tmp_path, {"audio/1.mp3": b""}, document=document)
    with pytest.raises(ValidationError) as info:
        validate(path)
    assert info.value.xsd_errors and [e["location"] for e in info.value.archive_errors] == ["audio/1.mp3"]
    assert "Archive validation failed" in str(info.value)


# Referenced parts: an image (<src>) and a linked attachment (<href>); "#x" refers into the document.
_REFERENCING = (
    '<doclang xmlns="https://www.doclang.ai/ns/v0"{version}><picture><src uri="assets/a.png"/></picture>'
    '<text><href uri="assets/c.png"/>Report</text><text><href uri="#x"/>here</text></doclang>'
)


def _warnings_and_errors(path: Path) -> tuple[list[str], list[tuple[str, str]]]:
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        errors = _archive_errors(path)
    return [str(w.message) for w in caught if "declared" not in str(w.message)], errors


def test_referenced_and_accounted_for_parts(tmp_path: Path):
    members: dict[str, bytes | str | None] = {
        "assets/a.png": b"",
        "assets/c.png": b"",
        "pages/1.png": b"",
        "_rels/.rels": _rels(("thumbnail", "assets/thumbnail.png")),  # any relationship accounts for its target
        "assets/thumbnail.png": b"",
        "assets/_rels/a.png.rels": _rels().replace('Target="document.xml"', 'Target="b.png"'),  # of a part
        "assets/b.png": b"",
    }
    assert _warnings_and_errors(_archive(tmp_path, members, document=_REFERENCING.format(version=""))) == ([], [])


def test_missing_and_unaccounted_for_parts(tmp_path: Path):
    members = {"pages/cover.png": b"", "notes.png": b"", "assets/b.png": b""}
    found = _warnings_and_errors(_archive(tmp_path, members, document=_REFERENCING.format(version="")))
    assert found == (
        [
            f"{part}: Not referenced by the markup or a relationship, nor a page image or whole-track media"
            for part in ("pages/cover.png", "notes.png", "assets/b.png")
        ],
        [("document.xml", "The <src> URI of 'assets/a.png' does not resolve to a part of the archive")],
    )


@pytest.mark.parametrize(("version", "applies"), [("0.9", False), ("0.10", True)])
def test_reference_rules_apply_from_0_10(tmp_path: Path, version: str, applies: bool):
    """The archive rules apply as of the declared version, even one without schemas of its own."""
    document = _REFERENCING.format(version=f' version="{version}"')
    found = _warnings_and_errors(_archive(tmp_path, {"assets/b.png": b""}, document=document))
    assert (found != ([], [])) is applies


# The source rules apply from 0.10.
_SOURCE_DOCUMENT = _DOCUMENT.replace('version="0.9"', 'version="0.10"')
_DESCRIPTOR = b'<source xmlns="http://doclang.ai/ns/package/2026/source-metadata" name="episode.mp3"/>'
_DESCRIPTOR_TYPE = (
    '<Override PartName="/source-metadata.xml" ContentType="application/vnd.doclang.source-metadata+xml"/></Types>'
)


@pytest.mark.filterwarnings("ignore:No schema for declared DocLang version 0.10")
@pytest.mark.parametrize(
    "members",
    [
        {"_rels/.rels": _rels(("source", "source.mp3")), "source.mp3": b""},
        {"_rels/.rels": _rels(("source", "/audio/1.mp3")), "audio/1.mp3": b""},  # an existing part, no second copy
        {
            "_rels/.rels": _rels(("source", "source")),
            "source": b"%PDF",
            "[Content_Types].xml": _CONTENT_TYPES.replace(
                "</Types>", '<Override PartName="/SOURCE" ContentType="application/pdf"/></Types>'
            ),
        },
        {
            "_rels/.rels": _rels(("source", "source.mp3"), ("source-metadata", "source-metadata.xml")),
            "source.mp3": b"",
            "source-metadata.xml": _DESCRIPTOR,
            "[Content_Types].xml": _CONTENT_TYPES.replace("</Types>", _DESCRIPTOR_TYPE),
        },
    ],
)
def test_valid_archive_with_source(tmp_path: Path, members):
    assert _archive_errors(_archive(tmp_path, members, document=_SOURCE_DOCUMENT)) == []


@pytest.mark.filterwarnings("ignore:No schema for declared DocLang version 0.10")
@pytest.mark.parametrize(
    ("members", "location", "message"),
    [
        ({"_rels/.rels": _rels(("source", "source.mp3"))}, "_rels/.rels", "The source part 'source.mp3' is missing"),
        ({"_rels/.rels": _rels(("source", "source.pdf")), "source.pdf": b""}, "source.pdf", "No content type"),
        (
            {"_rels/.rels": _rels(("source", "http://example.com/a.pdf"))},
            "_rels/.rels",
            "must target a part of the archive",
        ),
        (
            {"_rels/.rels": _rels(("source", "a.mp3"), ("source", "b.mp3")), "a.mp3": b"", "b.mp3": b""},
            "_rels/.rels",
            "More than one http://doclang.ai/ns/package/2026/relationships/source relationship",
        ),
        (
            {"_rels/.rels": _rels(("source-metadata", "s.mp3")), "s.mp3": _DESCRIPTOR},
            "_rels/.rels",
            "source-metadata relationship without a source relationship",
        ),
        (
            {"_rels/.rels": _rels(("source", "a.mp3"), ("source-metadata", "s.mp3")), "a.mp3": b"", "s.mp3": b"<x/>"},
            "s.mp3",
            "The root element must be source",
        ),
    ],
)
def test_invalid_archive_with_source(tmp_path: Path, members, location, message):
    errors = _archive_errors(_archive(tmp_path, members, document=_SOURCE_DOCUMENT))
    assert [e[0] for e in errors] == [location]
    assert message in errors[0][1]
