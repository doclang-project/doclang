"""Validate DocLang XML snippets embedded in normative Markdown documentation."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.validate_markdown_snippets import (  # noqa: E402
    _DEFAULT_MARKDOWN_FILES,
    _validate_markdown_files,
)


def test_documentation_xml_snippets_are_valid() -> None:
    results = _validate_markdown_files(list(_DEFAULT_MARKDOWN_FILES))
    failures = [result for result in results if result.error]
    assert results, "expected at least one XML snippet in documentation"
    assert not failures, "\n\n".join(
        f"{result.snippet.source}:{result.snippet.line}\n{result.error}" for result in failures
    )
