"""
Tests for the DocLang CLI.

Tests the command-line interface using Typer's CliRunner.
"""

import json
from pathlib import Path
from typer.testing import CliRunner

from doclang.cli import app

runner = CliRunner()


def test_validate_valid_document():
    """Test validating a valid document."""
    xml_file = Path("tests/data/valid/comprehensive.dclg.xml")
    result = runner.invoke(app, ["validate", str(xml_file)])
    assert result.exit_code == 0


def test_validate_invalid_document():
    """Test validating an invalid document."""
    xml_file = Path("tests/data/invalid_schematron/hyperlink_invalid_content.dclg.xml")
    result = runner.invoke(app, ["validate", str(xml_file)])
    assert result.exit_code == 1
