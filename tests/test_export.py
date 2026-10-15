"""Tests for HTML comment handling in export_docx."""

from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import pytest
from lxml import etree

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.export_docx import _strip_html_comments_outside_code, build_document, markdown_anchor  # noqa: E402


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


@pytest.mark.parametrize(
    ("heading", "anchor"),
    [
        ("`<audio>`", "audio"),
        ("`<field_heading>`", "field_heading"),
        ("DocLang archive format", "doclang-archive-format"),
        ("Annex A (normative): Reference", "annex-a-normative-reference"),
        ("Annex D (informative): Future extensions", "annex-d-informative-future-extensions"),
        ("Annex A <br/> (normative) <br/> Reference", "annex-a--normative--reference"),  # as GitHub does
        ("A **bold** heading, with punctuation!", "a-bold-heading-with-punctuation"),
    ],
)
def test_markdown_anchor_follows_github_heading_slugs(heading: str, anchor: str) -> None:
    assert markdown_anchor(heading) == anchor


def _unresolved_internal_links(docx_path: Path) -> list[str]:
    word = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    root = etree.fromstring(zipfile.ZipFile(docx_path).read("word/document.xml"))
    bookmarks = {b.get(word + "name") for b in root.iter(word + "bookmarkStart")}
    anchors = {h.get(word + "anchor") for h in root.iter(word + "hyperlink") if h.get(word + "anchor")}
    return sorted(a for a in anchors if a not in bookmarks)


def test_links_to_headings_with_punctuation_resolve_in_the_export(tmp_path: Path) -> None:
    md = tmp_path / "doc.md"
    md.write_text(
        "# Title\n\n## Annexes\n\n### Annex A (normative): Reference\n\nText.\n\n"
        "### Other\n\nSee [Reference](#annex-a-normative-reference) and [Annexes](#annexes).\n",
        encoding="utf-8",
    )
    out = tmp_path / "doc.docx"
    build_document(md, out, apply_template_style=False)
    assert _unresolved_internal_links(out) == []


def test_every_internal_link_in_the_exported_spec_resolves(tmp_path: Path) -> None:
    out = tmp_path / "spec.docx"
    build_document(ROOT / "spec.md", out, apply_template_style=False)
    assert _unresolved_internal_links(out) == []
