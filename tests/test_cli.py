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
    assert "No schema for DocLang spec version '9.9'" in bad.output


def test_cli_warns_when_version_undeclared(tmp_path):
    doc = tmp_path / "doc.dclg"
    doc.write_text('<doclang xmlns="https://www.doclang.ai/ns/v0"><text>hi</text></doclang>', encoding="utf-8")
    result = runner.invoke(app, ["validate", str(doc), "--xsd-only"])
    assert result.exit_code == 0, result.output
    assert "No DocLang version declared" in result.output


def _doc_with_version(tmp_path, version):
    doc = tmp_path / "doc.dclg"
    doc.write_text(f'<doclang xmlns="https://www.doclang.ai/ns/v0" version="{version}"/>', encoding="utf-8")
    return doc


def test_cli_explains_version_rewrite_and_strict_flag(tmp_path):
    doc = _doc_with_version(tmp_path, "0.8")
    lenient = runner.invoke(app, ["validate", str(doc), "--xsd-only", "--spec-version", "0.7"])
    assert lenient.exit_code == 0, lenient.output
    assert "Warning: Document declares version 0.8; validating as 0.7 as requested." in lenient.output
    assert 'Note: The 0.7 XSD only accepts version "0.7"' in lenient.output

    strict = runner.invoke(
        app, ["validate", str(doc), "--xsd-only", "--spec-version", "0.7", "--strict-xsd-version-attr"]
    )
    assert strict.exit_code == 1
    assert "Note:" not in strict.output


def test_cli_json_output_includes_notes(tmp_path):
    import json

    doc = _doc_with_version(tmp_path, "0.8")
    result = runner.invoke(app, ["validate", str(doc), "--xsd-only", "--spec-version", "0.7", "--format", "json"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert len(payload["notes"]) == 2
    assert payload["notes"][0].startswith("Document declares version 0.8")


def test_cli_strict_declared_version(tmp_path):
    doc = _doc_with_version(tmp_path, "0.1")
    lenient = runner.invoke(app, ["validate", str(doc), "--xsd-only"])
    assert lenient.exit_code == 0, lenient.output
    assert "No schema for declared DocLang version 0.1" in lenient.output

    strict = runner.invoke(app, ["validate", str(doc), "--xsd-only", "--strict-declared-version"])
    assert strict.exit_code == 1
    assert "No schema for declared DocLang version '0.1'" in strict.output
