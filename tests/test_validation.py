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
from doclang import SchematronBackendNotFound, SchematronViolation, ValidationError, validate

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
