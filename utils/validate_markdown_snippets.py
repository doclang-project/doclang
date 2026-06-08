#!/usr/bin/env python3
"""
Extract DocLang XML snippets from Markdown files and validate them.

Snippets are fenced code blocks tagged ``xml``. Before validation:

- Standalone ``...`` lines (structural ellipsis placeholders) become ``<!--...-->``.
- Fragments that do not start with ``<doclang>`` are wrapped in a root ``<doclang>`` element.
- The DocLang namespace is injected when missing (``allow_empty_namespace``).

Usage::

    uv run python utils/validate_markdown_snippets.py
    uv run python utils/validate_markdown_snippets.py spec.md examples/form/form-examples.md
    uv run python utils/validate_markdown_snippets.py --fix spec.md
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from doclang import ValidationError, validate

_XML_FENCE_RE = re.compile(r"^```xml\n(.*?)^```", re.MULTILINE | re.DOTALL)
_TOP_LEVEL_ELLIPSIS_RE = re.compile(r"^(\s*)\.\.\.(\s*)$")
_UNCLOSED_NL_RE = re.compile(r"<nl>(?!/)")

_DEFAULT_MARKDOWN_FILES = (
    Path("spec.md"),
    Path("examples/form/form-examples.md"),
)


@dataclass(frozen=True)
class _MarkdownSnippet:
    source: Path
    line: int
    content: str


@dataclass(frozen=True)
class _SnippetValidationResult:
    snippet: _MarkdownSnippet
    error: str | None = None


def _html_comment_ranges(text: str) -> list[tuple[int, int]]:
    ranges: list[tuple[int, int]] = []
    index = 0
    while True:
        start = text.find("<!--", index)
        if start == -1:
            break
        end = text.find("-->", start)
        if end == -1:
            break
        ranges.append((start, end + 3))
        index = end + 3
    return ranges


def _in_html_comment(position: int, ranges: list[tuple[int, int]]) -> bool:
    return any(start <= position < end for start, end in ranges)


def _extract_xml_snippets(markdown_path: Path, *, skip_html_comments: bool = True) -> list[_MarkdownSnippet]:
    text = markdown_path.read_text(encoding="utf-8")
    comment_ranges = _html_comment_ranges(text) if skip_html_comments else []
    snippets: list[_MarkdownSnippet] = []
    for match in _XML_FENCE_RE.finditer(text):
        if skip_html_comments and _in_html_comment(match.start(), comment_ranges):
            continue
        content = match.group(1).rstrip("\n")
        line = text[: match.start()].count("\n") + 1
        snippets.append(_MarkdownSnippet(source=markdown_path, line=line, content=content))
    return snippets


def _replace_top_level_ellipsis(content: str) -> str:
    lines: list[str] = []
    for line in content.split("\n"):
        if _TOP_LEVEL_ELLIPSIS_RE.match(line):
            lines.append(_TOP_LEVEL_ELLIPSIS_RE.sub(r"\1<!--...-->\2", line))
        else:
            lines.append(line)
    return "\n".join(lines)


def _prepare_snippet_for_validation(content: str) -> str:
    content = _replace_top_level_ellipsis(content)
    content = _UNCLOSED_NL_RE.sub("<nl/>", content)
    stripped = content.strip()
    if not stripped.lower().startswith("<doclang"):
        content = f"<doclang>\n{content}\n</doclang>"
    return content


def _validate_snippet_content(content: str, *, label: str) -> None:
    prepared = _prepare_snippet_for_validation(content)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xml", delete=False, encoding="utf-8") as handle:
        handle.write(prepared)
        handle.flush()
        validate(handle.name, allow_empty_namespace=True)


def _validate_snippets(snippets: list[_MarkdownSnippet]) -> list[_SnippetValidationResult]:
    results: list[_SnippetValidationResult] = []
    for snippet in snippets:
        try:
            _validate_snippet_content(snippet.content, label=str(snippet.source))
            results.append(_SnippetValidationResult(snippet=snippet))
        except ValidationError as exc:
            results.append(_SnippetValidationResult(snippet=snippet, error=str(exc)))
        except Exception as exc:
            results.append(_SnippetValidationResult(snippet=snippet, error=str(exc)))
    return results


def _validate_markdown_files(paths: list[Path]) -> list[_SnippetValidationResult]:
    snippets: list[_MarkdownSnippet] = []
    for path in paths:
        snippets.extend(_extract_xml_snippets(path))
    return _validate_snippets(snippets)


def _fix_top_level_ellipsis_in_markdown(markdown_path: Path) -> int:
    text = markdown_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    in_xml_fence = False
    replacements = 0

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "```xml":
            in_xml_fence = True
            continue
        if in_xml_fence and stripped == "```":
            in_xml_fence = False
            continue
        if in_xml_fence and _TOP_LEVEL_ELLIPSIS_RE.match(line.rstrip("\n")):
            new_line = _TOP_LEVEL_ELLIPSIS_RE.sub(r"\1<!--...-->\2", line.rstrip("\n"))
            if line.endswith("\n"):
                new_line += "\n"
            if new_line != line:
                lines[index] = new_line
                replacements += 1

    if replacements:
        markdown_path.write_text("".join(lines), encoding="utf-8")
    return replacements


def _format_failure(result: _SnippetValidationResult) -> str:
    snippet = result.snippet
    location = f"{snippet.source}:{snippet.line}"
    message = result.error or "unknown error"
    return f"{location}\n{message}"


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate DocLang XML snippets embedded in Markdown files.")
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="Markdown files to process (default: spec.md and examples/form/form-examples.md)",
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Replace top-level standalone ... lines with <!--...--> inside ```xml fences",
    )
    args = parser.parse_args(argv)

    paths = args.files or list(_DEFAULT_MARKDOWN_FILES)
    missing = [path for path in paths if not path.exists()]
    if missing:
        for path in missing:
            print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    if args.fix:
        total = 0
        for path in paths:
            count = _fix_top_level_ellipsis_in_markdown(path)
            if count:
                print(f"Updated {count} ellipsis placeholder(s) in {path}")
            total += count
        if total == 0:
            print("No top-level ellipsis placeholders found.")
        return 0

    results = _validate_markdown_files(paths)
    failures = [result for result in results if result.error]
    print(f"Validated {len(results)} snippet(s) from {len(paths)} file(s).")
    if not failures:
        print("All snippets are valid.")
        return 0

    print(f"{len(failures)} snippet(s) failed validation:", file=sys.stderr)
    for result in failures:
        print(file=sys.stderr)
        print(_format_failure(result), file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(_main())
