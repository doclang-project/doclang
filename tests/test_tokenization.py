"""Cross-check doclang.tokenization against the spec's "Token vocabulary" table."""

from __future__ import annotations

import re
from pathlib import Path

from doclang.tokenization import get_special_tokens

SPEC_PATH = Path(__file__).resolve().parents[1] / "spec.md"

_ROW_RE = re.compile(r"^\|(.+)\|(.+)\|\s*$", re.MULTILINE)
_BACKTICK_RE = re.compile(r"`([^`]*)`")
_RANGE_TOKEN_RE = re.compile(r'^(<\w+ value=")(\d+)("/>)$')


def _parse_range_token(token: str) -> tuple[str, int, str]:
    match = _RANGE_TOKEN_RE.match(token)
    assert match is not None, f'not a `<name value="N"/>` token: {token!r}'
    return match.group(1), int(match.group(2)), match.group(3)


def _expand_range_row(backticked: list[str]) -> list[str]:
    """Expand a ``...`` token-vocabulary row (e.g. ``<location value="0"/>``, ``<location
    value="1"/>``, ..., ``<location value="511"/>``) into every concrete token, inferring the
    step from the first two listed values and the bounds from the first and last."""
    prefix, first, suffix = _parse_range_token(backticked[0])
    _, second, _ = _parse_range_token(backticked[1])
    _, last, _ = _parse_range_token(backticked[-1])
    step = second - first
    return [f"{prefix}{value}{suffix}" for value in range(first, last + 1, step)]


def _tokens_from_spec() -> list[str]:
    text = SPEC_PATH.read_text()
    section = text[text.index("#### Token vocabulary") : text.index("### Future Extensions")]

    tokens: list[str] = []
    for match in _ROW_RE.finditer(section):
        column = match.group(1).strip()
        if column in ("Token", "---") or not column.startswith("`"):
            continue
        if "..." in column:
            tokens.extend(_expand_range_row(_BACKTICK_RE.findall(column)))
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
