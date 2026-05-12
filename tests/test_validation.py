"""
Pytest test suite for DocLang XML schema validation.

Tests both valid and invalid XML documents against XSD and Schematron rules.
"""

import pytest
from pathlib import Path
from doclang.xsd_validation import _validate_xsd
from doclang.schematron_validation import _validate_with_schematron


# Paths
PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_DIR = PROJECT_ROOT / "doclang"
XSD_FILE = SCHEMA_DIR / "doclang.xsd"
SCH_FILE = SCHEMA_DIR / "doclang.sch"
TEST_DATA_DIR = Path(__file__).parent / "data"
VALID_DIR = TEST_DATA_DIR / "valid"
INVALID_XSD_DIR = TEST_DATA_DIR / "invalid_xsd"
INVALID_SCHEMATRON_DIR = TEST_DATA_DIR / "invalid_schematron"


# Collect test files
valid_files = list(VALID_DIR.glob("*.dclg.xml")) if VALID_DIR.exists() else []
invalid_files = list(INVALID_SCHEMATRON_DIR.glob("*.dclg.xml")) if INVALID_SCHEMATRON_DIR.exists() else []
invalid_xsd_files = list(INVALID_XSD_DIR.glob("*.dclg.xml")) if INVALID_XSD_DIR.exists() else []


@pytest.mark.parametrize("xml_file", valid_files, ids=lambda f: f.stem)
def test_valid_xsd(xml_file):
    """Test that valid XML files pass XSD validation."""
    # Special handling for no_namespace test - requires flag
    # Handle .dclg.xml double extension: remove both extensions to get base name
    base_name = xml_file.name.replace('.dclg.xml', '')
    allow_empty = base_name == "no_namespace"
    is_valid, errors = _validate_xsd(xml_file, XSD_FILE, allow_empty_namespace=allow_empty)
    if not is_valid:
        error_msgs = []
        for error in errors:
            if "line" in error:
                error_msgs.append(f"Line {error['line']}: {error['message']}")
            else:
                error_msgs.append(error.get('error', 'Unknown error'))
        pytest.fail(f"XSD validation failed for {xml_file.name}:\n" + "\n".join(error_msgs))


@pytest.mark.parametrize("xml_file", valid_files, ids=lambda f: f.stem)
def test_valid_schematron(xml_file):
    """Test that valid XML files pass Schematron validation."""
    # Special handling for no_namespace test - requires flag
    # Handle .dclg.xml double extension: remove both extensions to get base name
    base_name = xml_file.name.replace('.dclg.xml', '')
    allow_empty = base_name == "no_namespace"
    is_valid, failed_asserts = _validate_with_schematron(
        xml_file,
        sch_file=SCH_FILE,
        allow_empty_namespace=allow_empty,
        verbose=False
    )
    if not is_valid:
        error_msgs = []
        for assert_elem in failed_asserts:
            location = assert_elem.get("location", "unknown")
            text_elem = assert_elem.find("{http://purl.oclc.org/dsdl/svrl}text")
            message = text_elem.text if text_elem is not None else "No message"
            error_msgs.append(f"{location}: {message}")
        pytest.fail(f"Schematron validation failed for {xml_file.name}:\n" + "\n".join(error_msgs))


@pytest.mark.parametrize("xml_file", invalid_files, ids=lambda f: f.stem)
def test_invalid_schematron(xml_file):
    """Test that invalid XML files fail Schematron validation."""
    is_valid, failed_asserts = _validate_with_schematron(xml_file, sch_file=SCH_FILE, verbose=False)
    assert not is_valid, f"Expected Schematron validation to fail for {xml_file.name}, but it passed"
    assert len(failed_asserts) > 0, f"Expected validation errors for {xml_file.name}"


@pytest.mark.parametrize("xml_file", invalid_xsd_files, ids=lambda f: f.stem)
def test_invalid_xsd(xml_file):
    """Test that invalid XML files fail XSD validation."""
    is_valid, errors = _validate_xsd(xml_file, XSD_FILE, allow_empty_namespace=False)
    assert not is_valid, f"Expected XSD validation to fail for {xml_file.name}, but it passed"
    assert len(errors) > 0, f"Expected validation errors for {xml_file.name}"


def test_schema_files_exist():
    """Test that required schema files exist."""
    assert XSD_FILE.exists(), f"XSD file not found: {XSD_FILE}"
    assert SCH_FILE.exists(), f"Schematron file not found: {SCH_FILE}"


def test_test_directories_exist():
    """Test that test directories exist and contain files."""
    assert VALID_DIR.exists(), f"Valid test directory not found: {VALID_DIR}"
    assert INVALID_SCHEMATRON_DIR.exists(), f"Invalid test directory not found: {INVALID_SCHEMATRON_DIR}"
    assert INVALID_XSD_DIR.exists(), f"Invalid XSD test directory not found: {INVALID_XSD_DIR}"
    assert len(valid_files) > 0, "No valid test files found"
    assert len(invalid_files) > 0, "No invalid test files found"
    assert len(invalid_xsd_files) > 0, "No invalid XSD test files found"
