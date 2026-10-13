"""
Pytest test suite for DocLang XML schema validation.

Tests both valid and invalid XML documents against XSD and Schematron rules
via the public ``validate()`` API.
"""

import builtins
import sys
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
from doclang.utils import _DTD_REJECTED_MESSAGE, _write_xml_without_dtd

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
    """A package-like schema dir: latest schemas at 1.2, plus older ones at 0.7 and 1.0."""
    import shutil

    from doclang import _schemas

    root = tmp_path / "pkg"
    root.mkdir()
    xsd = (SCHEMA_DIR / "doclang.xsd").read_text(encoding="utf-8")
    current = _schemas._current_version()
    for name in ("0.7", "1.0"):
        folder = root / "schemas" / name
        folder.mkdir(parents=True)
        (folder / "doclang.xsd").write_text(xsd.replace(f'version="{current}.', f'version="{name}.'), encoding="utf-8")
        shutil.copy(SCHEMA_DIR / "doclang.sch", folder / "doclang.sch")
    (root / "doclang.xsd").write_text(xsd.replace(f'version="{current}.', 'version="1.2.'), encoding="utf-8")
    shutil.copy(SCHEMA_DIR / "doclang.sch", root / "doclang.sch")
    monkeypatch.setattr(_schemas, "_SCHEMA_DIR", root)
    return root


def test_select_schemas_precedence(schema_dir, tmp_path):
    from doclang._schemas import _select_schemas

    assert _select_schemas(_doc(tmp_path, "0.7")).version == "0.7"
    assert _select_schemas(_doc(tmp_path, "0.7"), "1.2").version == "1.2"  # explicit override wins
    unversioned = _select_schemas(_doc(tmp_path, None))
    assert (unversioned.version, unversioned.declared) == ("1.2", False)


def test_select_schemas_major_one_falls_back_to_newer_minor(schema_dir, tmp_path):
    from doclang._schemas import UnsupportedVersionError, _select_schemas

    assert _select_schemas(_doc(tmp_path, "1.1")).version == "1.2"  # 1.1 instance, 1.2 schema
    with pytest.raises(UnsupportedVersionError):
        _select_schemas(_doc(tmp_path, "1.3"))  # newer than supported
    with pytest.raises(UnsupportedVersionError):
        _select_schemas(_doc(tmp_path, "0.8"))  # no fallback within 0.x


def test_validate_unversioned_warns():
    path = VALID_DIR / "ok_no_namespace.dclg"
    with pytest.warns(UserWarning, match="No DocLang version declared"):
        validate(path, allow_empty_namespace=True)


def test_validate_explicit_spec_version(schema_dir, tmp_path):
    validate(_doc(tmp_path, "1.2"), xsd_only=True, spec_version="1.2")
    with pytest.raises(UnsupportedVersionError, match="supported versions"):
        validate(_doc(tmp_path, "1.2"), xsd_only=True, spec_version="9.9")


def test_validate_unsupported_declared_version_is_validation_error(tmp_path):
    with pytest.raises(ValidationError, match=r"Unsupported DocLang spec version '0\.1'"):
        validate(_doc(tmp_path, "0.1"), xsd_only=True)


def test_version_attribute_only_constrained_to_format(tmp_path):
    """The XSD does not tie the declared version to the schema: a 0.8-declared doc validates as 0.7."""
    with pytest.warns(UserWarning):
        assert validate(_doc(tmp_path, "0.8"), xsd_only=True, spec_version="0.7") is None
        with pytest.raises(ValidationError):
            validate(_doc(tmp_path, "v1"), xsd_only=True, spec_version="0.7")  # not MAJOR.MINOR


def test_validate_notes_override_differing_from_declared(tmp_path):
    with pytest.warns(UserWarning, match="declares version 0.8; validating as 0.7"):
        validate(_doc(tmp_path, "0.8"), xsd_only=True, spec_version="0.7")
