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
    xml_file = Path("tests/data/valid/ok_comprehensive.dclg")
    result = runner.invoke(app, ["validate", str(xml_file)])
    assert result.exit_code == 0


def test_validate_invalid_document():
    """Test validating an invalid document."""
    xml_file = Path("tests/data/invalid/nok_href_in_body.dclg")
    result = runner.invoke(app, ["validate", str(xml_file)])
    assert result.exit_code == 1


def test_cli_spec_version_override_and_unsupported(tmp_path):
    doc = tmp_path / "doc.dclg"
    doc.write_text('<doclang xmlns="https://www.doclang.ai/ns/v0"><text>hi</text></doclang>', encoding="utf-8")
    ok = runner.invoke(app, ["validate", str(doc), "--xsd-only", "--spec-version", "0.7"])
    assert ok.exit_code == 0, ok.output
    bad = runner.invoke(app, ["validate", str(doc), "--xsd-only", "--spec-version", "9.9"])
    assert bad.exit_code == 1
    assert "Unsupported DocLang spec version '9.9'" in bad.output


def test_cli_warns_when_version_undeclared(tmp_path):
    doc = tmp_path / "doc.dclg"
    doc.write_text('<doclang xmlns="https://www.doclang.ai/ns/v0"><text>hi</text></doclang>', encoding="utf-8")
    result = runner.invoke(app, ["validate", str(doc), "--xsd-only"])
    assert result.exit_code == 0, result.output
    assert "No DocLang version declared" in result.output
