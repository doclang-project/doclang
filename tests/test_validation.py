"""
Pytest test suite for DocLang XML schema validation.

Tests both valid and invalid XML documents against XSD and Schematron rules
via the public ``validate()`` API.
"""

from pathlib import Path

import pytest

import doclang
from doclang import ValidationError, validate

TEST_DATA_DIR = Path(__file__).parent / "data"
VALID_DIR = TEST_DATA_DIR / "valid"
INVALID_DIR = TEST_DATA_DIR / "invalid"
SCHEMA_DIR = Path(doclang.__file__).resolve().parent


# Collect test files
valid_files = list(VALID_DIR.glob("*.dclg.xml")) if VALID_DIR.exists() else []
invalid_files = list(INVALID_DIR.glob("*.dclg.xml")) if INVALID_DIR.exists() else []


def _allow_empty_namespace(xml_file: Path) -> bool:
    base_name = xml_file.name.replace(".dclg.xml", "")
    return base_name in ["ok_no_namespace", "doclang_example"]


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
    assert not (exc.xsd_valid and exc.schematron_valid), f"Expected {xml_file.name} to fail validation, but it passed"

    if not exc.xsd_valid:
        assert len(exc.xsd_errors) > 0, f"Expected XSD validation errors for {xml_file.name}"
    if not exc.schematron_valid:
        assert len(exc.schematron_errors) > 0, f"Expected Schematron validation errors for {xml_file.name}"


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
