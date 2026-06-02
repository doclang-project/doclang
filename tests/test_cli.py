"""
Tests for the DocLang CLI.

Tests the command-line interface using Typer's CliRunner.
"""

from importlib.metadata import version
from pathlib import Path

from typer.testing import CliRunner

from doclang.cli import app
from doclang.utils import _VERSION
from doclang.version import _version_from_describe

runner = CliRunner()


def test_version_from_describe():
    assert _version_from_describe("v0.3.0") == "0.3.0"
    assert _version_from_describe("v0.3.0-3-g93c2a53") == "0.3.0+g93c2a53"
    assert _version_from_describe("v0.3.0-3-g93c2a53-dirty").startswith("0.3.0+g93c2a53.d")


def test_cli_version_matches_installed_metadata():
    expected = version("doclang")
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert _VERSION == expected
    assert expected in result.stdout


def test_validate_valid_document():
    """Test validating a valid document."""
    xml_file = Path("tests/data/valid/ok_comprehensive.dclg.xml")
    result = runner.invoke(app, ["validate", str(xml_file)])
    assert result.exit_code == 0


def test_validate_invalid_document():
    """Test validating an invalid document."""
    xml_file = Path("tests/data/invalid/nok_href_in_body.dclg.xml")
    result = runner.invoke(app, ["validate", str(xml_file)])
    assert result.exit_code == 1
