"""Tests for HTML comment handling in export_docx."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.export_docx import _strip_html_comments_outside_code  # noqa: E402


def test_strip_prose_comments() -> None:
    assert _strip_html_comments_outside_code("Hello <!-- hidden --> world") == "Hello  world"


def test_preserve_fenced_code_comments() -> None:
    md = "```xml\n<!-- keep me -->\n```"
    assert _strip_html_comments_outside_code(md) == md


def test_preserve_inline_code_comments() -> None:
    md = "Use `<!-- comment -->` here"
    assert _strip_html_comments_outside_code(md) == md


def test_strip_prose_but_preserve_inline_code_on_same_line() -> None:
    md = "See `foo <!-- bar -->` and <!-- prose --> end"
    assert _strip_html_comments_outside_code(md) == "See `foo <!-- bar -->` and  end"


def test_strip_prose_comments_inside_html_comment_with_fences() -> None:
    md = "Before\n<!-- commented out section\n\n```xml\n<doclang/>\n```\n-->\nAfter\n"
    assert _strip_html_comments_outside_code(md) == "Before\n\nAfter\n"


def test_strip_appendix_note_comment_from_spec() -> None:
    md = Path(__file__).resolve().parents[1] / "spec.md"
    stripped = _strip_html_comments_outside_code(md.read_text(encoding="utf-8"))
    assert "NOTE: do not edit Appendix A" not in stripped
    assert "Component-level metadata" not in stripped
    assert "deriveable from the document" not in stripped
    assert not stripped.rstrip().endswith("-->")
    assert "<!-- document head: -->" in stripped


def test_malformed_unclosed_inline_backtick_does_not_block_later_comment_stripping() -> None:
    md = "See `<element>; analogous to [`<other>`](#anchor)\n<!-- prose comment -->\nAfter\n"
    assert _strip_html_comments_outside_code(md) == ("See `<element>; analogous to [`<other>`](#anchor)\n\nAfter\n")
