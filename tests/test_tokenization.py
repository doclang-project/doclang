"""Cross-check doclang.tokenization against the spec's "Token vocabulary" table."""

from __future__ import annotations

import re
from pathlib import Path

from doclang.tokenization import DEFAULT_MAX_RESOLUTION, get_special_tokens

SPEC_PATH = Path(__file__).resolve().parents[1] / "spec.md"

_ROW_RE = re.compile(r"^\|(.+)\|(.+)\|\s*$", re.MULTILINE)
_BACKTICK_RE = re.compile(r"`([^`]*)`")


def _tokens_from_spec() -> list[str]:
    text = SPEC_PATH.read_text()
    section = text[text.index("#### Token vocabulary") : text.index("### Future Extensions")]

    tokens: list[str] = []
    for match in _ROW_RE.finditer(section):
        column = match.group(1).strip()
        if column in ("Token", "---") or not column.startswith("`"):
            continue
        if "..." in column:
            # The location row lists a `<location value="0"/>` ... `<location value="511"/>` range.
            tokens.extend(f'<location value="{value}"/>' for value in range(DEFAULT_MAX_RESOLUTION))
            continue
        tokens.extend(_BACKTICK_RE.findall(column))

    return tokens


def test_special_tokens_match_spec_vocabulary() -> None:
    assert set(get_special_tokens()) == set(_tokens_from_spec())


def test_special_tokens_have_no_duplicates() -> None:
    tokens = get_special_tokens()
    assert len(tokens) == len(set(tokens))


def test_location_tokens_respect_max_resolution() -> None:
    tokens = get_special_tokens(max_resolution=3)
    location_tokens = [t for t in tokens if t.startswith('<location value="')]
    assert location_tokens == ['<location value="0"/>', '<location value="1"/>', '<location value="2"/>']
