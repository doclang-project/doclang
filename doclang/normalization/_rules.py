# ruff: noqa: RUF001  # Unicode math and Greek letters are the subject matter
"""The normalization rules for super/subscripts, symbols and inline math (internal).

Each rule rewrites a representation that is equivalent to, but not, the preferred one of Annex C of the
specification ("Representing scripts, symbols and math"). Tier 1 rules are deterministic: what they rewrite has one
reading. Tier 2 rules are heuristics that read the surrounding text and can be wrong, e.g. for an ``x`` that is not
a variable.
"""

from __future__ import annotations

import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from lxml import etree

from doclang.migration._tree import location
from doclang.normalization import _tree as t
from doclang.normalization._latex import (
    ALL_SUPERSCRIPTS,
    GREEK,
    GREEK_FROM_LATEX,
    GREEK_LETTERS,
    SUBSCRIPTS,
    SUPERSCRIPT_LETTERS,
    needs_latex,
    script_text,
    to_latex,
)


class Context:
    """The document being normalized and the changes made to it."""

    def __init__(self, root: etree._Element) -> None:
        self.root = root
        self.changes: list[dict[str, Any]] = []
        self.rule: Rule | None = None

    def record(self, element: etree._Element, old: str, new: str) -> None:
        """Record a change by the current rule in the text block of ``element`` (call before removing it)."""
        assert self.rule is not None
        where = t.block(element)
        parent = where.getparent()
        if t.name(where) == "formula" and parent is not None and t.name(parent) in t.FORMULA_HOSTS:
            where = parent  # an inline formula: report its text block, which has a line
        self.changes.append(
            {
                "rule": self.rule.id,
                "tier": self.rule.tier,
                "location": location(where),
                "line": where.sourceline,
                "message": f"{old} → {new}",
            }
        )


@dataclass(frozen=True)
class Rule:
    id: str
    tier: int
    description: str
    apply: Callable[[Context], None]


# --------------------------------------------------------------------------------------------------------------
# shared patterns and helpers

_GREEK_CLASS = "[" + GREEK_LETTERS + "]"
_GREEK_SCRIPT = re.compile(r"[Ͱ-Ͽἀ-῿]{3,}")  # a Greek word: Greek-language text
_NUMBER = r"[-−]?\d+(?:[.,]\d+)?"
_ENDS_WITH_DIGIT = re.compile(r"\d\s?$")

# Single-letter chemical element symbols, units and unit prefixes.
_ELEMENTS_1 = frozenset("HBCNOFPSKVYIWU")
_UNIT_LETTERS = frozenset("mgslLKAVWJNCFTHhdtMΩ")
_UNIT_TOKENS = frozenset(
    "m g s l L K A V W J N C F T H h d t Pa Hz mol min eV Wb kg mg µg μg ng km cm mm µm μm nm ms µs μs ns kJ kW kV "
    "mA kPa MPa GPa kHz MHz GHz mL ml µL μL dL mmol µmol μmol nmol cal kcal".split()
)
_ORDINALS = frozenset({"st", "nd", "rd", "th", "er", "re", "e", "ème", "eme", "ª", "ᵉ"})
_RELATION = r"(?:<=|>=|=|<|>|≤|≥|≈|≠|∼|~|∝|≡|≪|≫)"


def _compact(latex: str) -> str:
    """``latex`` without whitespace, spacing commands, font commands and braces, for matching simple formulas."""
    s = re.sub(r"\\[,;:! ]|~", "", latex)
    s = re.sub(r"\\(?:mathrm|text|textrm|rm|mathit|mathsf|textsuperscript|operatorname)(?![A-Za-z])", "", s)
    return re.sub(r"[\s{}]", "", s)


def _inline_formula_text(formula: etree._Element) -> str | None:
    """The LaTeX of ``formula`` if it is an inline formula without children, else None."""
    parent = formula.getparent()
    if parent is None or t.name(parent) not in t.FORMULA_HOSTS:
        return None
    return t.plain_text(formula)


def _formulas(ctx: Context) -> list[etree._Element]:
    return [f for f in t.iter_named(ctx.root, "formula") if f.getparent() is not None and t.in_prose(f.getparent())]


def _scripts(ctx: Context, *names: str) -> list[etree._Element]:
    """Prose ``<superscript>``/``<subscript>`` elements (as named) without children, in document order."""
    return [
        e
        for e in ctx.root.iter()
        if t.name(e) in names and t.in_prose(e) and t.plain_text(e) is not None and t.plain_text(e)
    ]


def _attach_script(base: str, op: str, content: str) -> str:
    """``base`` with the script ``op{content}`` attached, grouping ``base`` if it already ends in such a script."""
    base = base.rstrip()
    if re.search(re.escape(op) + r"(?:\{[^{}]*\}|\\[A-Za-z]+|[^\s{}\\])$", base):
        base = "{" + base + "}"
    return f"{base}{op}{{{content}}}"


def _excerpt(old: str, new: str, context: int = 12) -> tuple[str, str]:
    """The part of ``old`` and ``new`` around where they differ, for a change message."""
    start = 0
    while start < min(len(old), len(new)) and old[start] == new[start]:
        start += 1
    end = 0
    while end < min(len(old), len(new)) - start and old[len(old) - 1 - end] == new[len(new) - 1 - end]:
        end += 1
    lo = max(0, start - context)

    def cut(s: str) -> str:
        hi = min(len(s), len(s) - end + context)
        return ("…" if lo else "") + s[lo:hi].strip() + ("…" if hi < len(s) else "")

    return cut(old), cut(new)


def _record_text(ctx: Context, slot: t.Slot, old: str, new: str) -> None:
    ctx.record(t.host(slot), *_excerpt(old, new))


def _number_latex(number: str) -> str:
    return number.replace("−", "-").replace(",", "{,}")


def _greek_language(element: etree._Element) -> bool:
    return bool(_GREEK_SCRIPT.search("".join(t.block(element).itertext())))


def _insert_formula_before(element: etree._Element, latex: str) -> etree._Element:
    parent = element.getparent()
    assert parent is not None
    formula = t.new_element(parent, "formula", latex)
    parent.insert(parent.index(element), formula)
    return formula


def _remove(element: etree._Element) -> None:
    """Remove ``element`` but keep the text after it."""
    t.replace_with_text(element, "")


def _for_each_match(
    ctx: Context,
    pattern: re.Pattern[str],
    hosts: frozenset[str],
    convert: Callable[[t.Slot, re.Match[str]], t.Slot | None],
    *,
    skip_greek_language: bool = False,
) -> None:
    """Call ``convert`` on each match of ``pattern`` in the prose slots whose host is in ``hosts``.

    ``convert`` returns the slot to continue in (the tail of the element it inserted), or None if it did nothing.
    """
    for slot in t.prose_slots(ctx.root):
        if t.name(t.host(slot)) not in hosts:
            continue
        if skip_greek_language and _greek_language(t.host(slot)):
            continue
        pos = 0
        while True:
            match = pattern.search(t.get(slot), pos)
            if match is None:
                break
            following = convert(slot, match)
            if following is None:
                pos = match.end()
            else:
                slot, pos = following, 0


# --------------------------------------------------------------------------------------------------------------
# tier 1


def celsius_fahrenheit(ctx: Context) -> None:
    for slot in t.prose_slots(ctx.root):
        text = t.get(slot)
        if "℃" in text or "℉" in text:
            new = text.replace("℃", "°C").replace("℉", "°F")
            _record_text(ctx, slot, text, new)
            t.put(slot, new)


_SCRIPT_RUN = re.compile(
    "(?P<sup>[" + "".join(ALL_SUPERSCRIPTS) + "]+)|(?P<sub>[" + "".join(SUBSCRIPTS) + "]+)",
)


def unicode_scripts(ctx: Context) -> None:
    hosts = t.SCRIPT_HOSTS - {"superscript", "subscript"}

    def convert(slot: t.Slot, match: re.Match[str]) -> t.Slot | None:
        run = match.group()
        text = t.get(slot)
        if match.group("sup") and all(c in SUPERSCRIPT_LETTERS for c in run):
            # modifier letters are phonetic (kʰ) unless they follow a number (2ⁿᵈ, 2.71ᵇᶠ)
            if not (match.start() and text[match.start() - 1].isdigit()):
                return None
        if match.group("sup"):
            local, content = "superscript", "".join(ALL_SUPERSCRIPTS[c] for c in run)
        else:
            local, content = "subscript", "".join(SUBSCRIPTS[c] for c in run)
        element = t.wrap_span(slot, match.start(), match.end(), local, content)
        ctx.record(element, run, t.markup(element))
        return (element, "tail")

    _for_each_match(ctx, _SCRIPT_RUN, hosts, convert)


def formula_formatting(ctx: Context) -> None:
    for formula in _formulas(ctx):
        inner = [
            e
            for e in reversed(list(formula.iter()))
            if e is not formula
            and t.name(e) in {"superscript", "subscript", "italic", "bold"}
            and t.block(e) is formula
        ]
        for element in inner:
            if len(element):
                continue
            text = element.text or ""
            old = t.markup(element)
            kind = t.name(element)
            slot = t.before(element)
            base = t.get(slot)
            if kind in {"superscript", "subscript"}:
                new = _attach_script(base, "^" if kind == "superscript" else "_", script_text(text))
                ctx.record(formula, old, new[len(base.rstrip()) :] if new.startswith(base.rstrip()) else new)
                t.put(slot, new)
                _remove(element)
            else:
                replacement = text if kind == "italic" else rf"\mathbf{{{text}}}"
                ctx.record(formula, old, replacement)
                t.replace_with_text(element, replacement)


def formula_unicode(ctx: Context) -> None:
    for formula in _formulas(ctx):
        slots: list[t.Slot] = [(formula, "text")]
        for child in formula:
            if t.name(child) == "content":
                slots.append((child, "text"))
            slots.append((child, "tail"))
        for slot in slots:
            text = t.get(slot)
            if needs_latex(text):
                new = to_latex(text)
                ctx.record(formula, *_excerpt(text, new, context=24))
                t.put(slot, new)


_TRADEMARK_SCRIPTS = {"TM": "™", "tm": "™", "™": "™", "SM": "℠", "℠": "℠", "®": "®", "(R)": "®", "©": "©"}
_TRADEMARK_FORMULAS = {
    "^TM": "™",
    "^tm": "™",
    r"\texttrademark": "™",
    r"^\texttrademark": "™",
    "^™": "™",
    r"\textregistered": "®",
    r"^\textregistered": "®",
    r"\circledR": "®",
    r"^\circledR": "®",
    "^®": "®",
    r"\copyright": "©",
    r"\textcopyright": "©",
    r"^\copyright": "©",
    "^©": "©",
}


def trademark(ctx: Context) -> None:
    for script in _scripts(ctx, "superscript"):
        text = (script.text or "").strip()
        if text in _TRADEMARK_SCRIPTS:
            ctx.record(script, t.markup(script), _TRADEMARK_SCRIPTS[text])
            t.replace_with_text(script, _TRADEMARK_SCRIPTS[text])
    for formula in _formulas(ctx):
        latex = _inline_formula_text(formula)
        if latex is None:
            continue
        char = _TRADEMARK_FORMULAS.get(_compact(latex))
        if char:
            ctx.record(formula, t.markup(formula), char)
            t.replace_with_text(formula, char)


_DEGREE = r"(?:\^?\\circ|\^?\\degree|\^?°)"
_DEGREE_FORMULA = re.compile(rf"(?P<number>{_NUMBER})?{_DEGREE}(?P<unit>[CF])?")
_DEGREE_O_FORMULA = re.compile(rf"(?P<number>{_NUMBER})?\^[oO0](?P<unit>[CF])")
_DEGREE_O_FORMULA_ALONE = re.compile(rf"(?P<number>{_NUMBER})?\^[oO]")
_TEMPERATURE_AFTER = re.compile(r"^\s?[CF](?![A-Za-z])")
_DEGREE_CHARS = re.compile(
    r"(?<=\d)( ?)[◦˚∘](?=\s?[CF](?![A-Za-z])|(?![A-Za-z0-9]))|(?<=\d)( ?)º(?=\s?[CF](?![A-Za-z]))"
)


def _degree_text(match: re.Match[str]) -> str:
    return (match.group("number") or "").replace("−", "-") + "°" + (match.group("unit") or "")


def degree(ctx: Context) -> None:
    for formula in _formulas(ctx):
        latex = _inline_formula_text(formula)
        if latex is None:
            continue
        compact = _compact(latex)
        match = _DEGREE_FORMULA.fullmatch(compact) or _DEGREE_O_FORMULA.fullmatch(compact)
        if match:
            ctx.record(formula, t.markup(formula), _degree_text(match))
            t.replace_with_text(formula, _degree_text(match))
    for script in _scripts(ctx, "superscript"):
        text = (script.text or "").strip()
        after_digit = bool(_ENDS_WITH_DIGIT.search(t.get(t.before(script))))
        temperature = bool(_TEMPERATURE_AFTER.match(script.tail or ""))
        if text in {"°", "◦", "˚", "∘"} or (after_digit and temperature and text in {"o", "O", "0", "º"}):
            ctx.record(script, t.markup(script), "°")
            t.replace_with_text(script, "°")
    for slot in t.prose_slots(ctx.root):
        text = t.get(slot)
        new = _DEGREE_CHARS.sub(lambda m: (m.group(1) or m.group(2) or "") + "°", text)
        if new != text:
            _record_text(ctx, slot, text, new)
            t.put(slot, new)


_ORDINAL_FORMULA = re.compile(r"(?P<number>\d+)?\^(?P<suffix>[^\^_\\]+)")


def ordinal_formula(ctx: Context) -> None:
    for formula in _formulas(ctx):
        latex = _inline_formula_text(formula)
        if latex is None:
            continue
        match = _ORDINAL_FORMULA.fullmatch(_compact(latex))
        if not match or match.group("suffix").lower() not in _ORDINALS:
            continue
        slot = t.before(formula)
        if not match.group("number") and not t.get(slot).endswith(tuple("0123456789")):
            continue
        parent = formula.getparent()
        assert parent is not None
        script = t.new_element(parent, "superscript", match.group("suffix"))
        ctx.record(formula, t.markup(formula), (match.group("number") or "") + t.markup(script))
        t.put(slot, t.get(slot) + (match.group("number") or ""))
        parent.insert(parent.index(formula), script)
        _remove(formula)


_EXPONENT = re.compile(r"\s*(?P<sign>[-−–+]?)\s*(?P<digits>\d+)\s*")
_SCIENTIFIC_BASE = re.compile(rf"(?<![\w.,])(?P<mantissa>{_NUMBER})\s*(?:×|x|X|\*|·|⋅|\\times)\s*10\s*$")


def _exponent(script: etree._Element) -> str | None:
    match = _EXPONENT.fullmatch(script.text or "")
    if not match:
        return None
    return ("-" if match.group("sign") in {"-", "−", "–"} else "") + match.group("digits")


def scientific_notation(ctx: Context) -> None:
    for script in _scripts(ctx, "superscript"):
        exponent = _exponent(script)
        parent = script.getparent()
        if exponent is None or parent is None or t.name(parent) not in t.FORMULA_HOSTS:
            continue
        slot = t.before(script)
        text = t.get(slot)
        match = _SCIENTIFIC_BASE.search(text)
        if not match:
            continue
        latex = rf"{_number_latex(match.group('mantissa'))} \times 10^{{{exponent}}}"
        old = text[match.start() :] + t.markup(script)
        t.put(slot, text[: match.start()])
        formula = _insert_formula_before(script, latex)
        ctx.record(formula, old.strip(), t.markup(formula))
        _remove(script)


def formula_script_merge(ctx: Context) -> None:
    for formula in _formulas(ctx):
        while _inline_formula_text(formula) is not None and not formula.tail:
            script = formula.getnext()
            if script is None or t.name(script) not in {"superscript", "subscript"} or t.plain_text(script) is None:
                break
            op = "^" if t.name(script) == "superscript" else "_"
            old = t.markup(formula) + t.markup(script)
            formula.text = _attach_script(formula.text or "", op, script_text(script.text or ""))
            ctx.record(formula, old, t.markup(formula))
            _remove(script)


_FORMULA_SEPARATOR = re.compile(r"\s*(?P<op>=|\+|-|−|×|·|⋅|<|>|≤|≥|≠|≈|±|∓|/|\*)?\s*")


def formula_merge(ctx: Context) -> None:
    for formula in _formulas(ctx):
        while formula.getparent() is not None and _inline_formula_text(formula) is not None:
            following = formula.getnext()
            if following is None or t.name(following) != "formula" or _inline_formula_text(following) is None:
                break
            separator = _FORMULA_SEPARATOR.fullmatch(formula.tail or "")
            if not separator:
                break
            op = separator.group("op")
            old = t.markup(formula) + (formula.tail or "") + t.markup(following)
            joint = f" {to_latex(op)} " if op else " "
            formula.text = (formula.text or "").rstrip() + joint + (following.text or "").lstrip()
            formula.tail = None
            ctx.record(formula, old, t.markup(formula))
            _remove(following)


# --------------------------------------------------------------------------------------------------------------
# tier 2


_DEGREE_O_TEXT = re.compile(r"(?<=\d)(\s?)[oO]\s?(?=[CF](?![A-Za-z]))")


def degree_ambiguous(ctx: Context) -> None:
    for formula in _formulas(ctx):
        latex = _inline_formula_text(formula)
        if latex is None:
            continue
        match = _DEGREE_O_FORMULA_ALONE.fullmatch(_compact(latex))
        if match and (match.group("number") or _ENDS_WITH_DIGIT.search(t.get(t.before(formula)))):
            ctx.record(formula, t.markup(formula), _degree_text(match))
            t.replace_with_text(formula, _degree_text(match))
    for script in _scripts(ctx, "superscript"):
        if (script.text or "").strip() in {"o", "O"} and _ENDS_WITH_DIGIT.search(t.get(t.before(script))):
            ctx.record(script, t.markup(script), "°")
            t.replace_with_text(script, "°")
    for slot in t.prose_slots(ctx.root):
        text = t.get(slot)
        new = _DEGREE_O_TEXT.sub(lambda m: m.group(1) + "°", text)
        if new != text:
            _record_text(ctx, slot, text, new)
            t.put(slot, new)


def greek_name_or_unit(ctx: Context) -> None:
    for formula in _formulas(ctx):
        latex = _inline_formula_text(formula)
        if latex is None:
            continue
        compact = _compact(latex)
        char = GREEK_FROM_LATEX.get(compact) or (compact if compact in GREEK else None)
        if char is None:
            continue
        before = t.get(t.before(formula))
        after = formula.tail or ""
        glued = bool(re.search(r"[\w-]$", before)) or bool(re.match(r"-?[A-Za-z]", after))
        unit = bool(_ENDS_WITH_DIGIT.search(before)) and bool(re.match(r"[A-Za-z]", after))
        if glued or unit:
            ctx.record(formula, t.markup(formula), char)
            t.replace_with_text(formula, char)


def label_noise(ctx: Context) -> None:
    for script in _scripts(ctx, "superscript", "subscript"):
        text = script.text or ""
        if not re.fullmatch(r"[a-z]", text) or t.name(t.block(script)) == "footnote":
            continue
        before = t.get(t.before(script))
        rest = re.match(r"[a-z]{2,}", script.tail or "")
        if before.strip() and before[-1].isspace() and rest:
            ctx.record(script, t.markup(script) + rest.group(), text + rest.group())
            t.replace_with_text(script, text)


_POWER_OF_TEN_BASE = re.compile(r"(?:^|(?<=[\s(\[~≈<>=]))10\s*$")


def power_of_ten(ctx: Context) -> None:
    for script in _scripts(ctx, "superscript"):
        exponent = _exponent(script)
        parent = script.getparent()
        if exponent is None or parent is None or t.name(parent) not in t.FORMULA_HOSTS:
            continue
        slot = t.before(script)
        text = t.get(slot)
        match = _POWER_OF_TEN_BASE.search(text)
        if not match or (match.start() == 0 and slot[1] == "tail"):
            continue
        old = text[match.start() :] + t.markup(script)
        t.put(slot, text[: match.start()])
        formula = _insert_formula_before(script, f"10^{{{exponent}}}")
        ctx.record(formula, old, t.markup(formula))
        _remove(script)


_SCRIPT_CONTENT = re.compile(rf"[-−+]?(?:[0-9A-Za-z]|{_GREEK_CLASS}){{1,4}}(?:[-−+][0-9A-Za-z]{{1,2}})?|[*'′″]")
_CHARGE = re.compile(r"\d*[+\-−]")
_VARIABLE_BASE = re.compile(rf"(?:^|(?<=[\s(\[{{=+\-−/,;:<>~≈]))(?P<coef>\d*)(?P<base>[A-Za-z]|{_GREEK_CLASS})$")
_NAME_BEFORE = re.compile(r"\b[A-Z][a-z]+,?\s+$")


def _unit_context(before: str) -> bool:
    """Whether the text before a single letter makes it a unit: a number, a unit or a slash."""
    if re.search(r"[/·⋅]\s*$", before):
        return True
    tokens = before.split()
    return bool(tokens) and (bool(re.fullmatch(_NUMBER + r"[%]?", tokens[-1])) or tokens[-1] in _UNIT_TOKENS)


def script_variable(ctx: Context) -> None:
    for script in _scripts(ctx, "superscript", "subscript"):
        parent = script.getparent()
        if parent is None or t.name(parent) not in t.FORMULA_HOSTS:
            continue
        content = (script.text or "").strip()
        subscript = t.name(script) == "subscript"
        if (
            not _SCRIPT_CONTENT.fullmatch(content)
            or content.lower() in _ORDINALS
            or content in _TRADEMARK_SCRIPTS
            or (not subscript and _CHARGE.fullmatch(content))
        ):
            continue
        tail = script.tail or ""
        if tail[:1].isalnum():  # glued to what follows: H₂O, x₁y₂
            continue

        previous = script.getprevious()
        italic = (
            previous is not None
            and t.name(previous) == "italic"
            and not previous.tail
            and re.fullmatch(rf"[A-Za-z]|{_GREEK_CLASS}", t.plain_text(previous) or "")
        )
        if italic:
            assert previous is not None
            coef, base = "", previous.text or ""
            context = t.get(t.before(previous))
            if context[-1:].isalnum():
                continue
        else:
            slot = t.before(script)
            text = t.get(slot)
            match = _VARIABLE_BASE.search(text)
            if not match or (match.start() == 0 and slot[1] == "tail"):
                continue
            coef, base = match.group("coef"), match.group("base")
            context = text[: match.start()]
            if base in _ELEMENTS_1 and subscript and content.isdigit():
                continue  # chemistry: O₂, N₂
            if base in _UNIT_LETTERS and (coef or _unit_context(context) or tail.lstrip().startswith("/")):
                continue  # a unit: 5 m², kg m⁻³, m/s²
            if not subscript and content.isdigit() and base.isupper() and _NAME_BEFORE.search(context):
                continue  # an initial with an affiliation mark: Smith J¹
        latex = coef + _attach_script(GREEK.get(base, base), "_" if subscript else "^", script_text(content))
        old = (coef + (t.markup(previous) if italic and previous is not None else base)) + t.markup(script)
        if italic:
            assert previous is not None
            formula = _insert_formula_before(previous, latex)
            _remove(previous)
        else:
            t.put(slot, context)
            formula = _insert_formula_before(script, latex)
        ctx.record(formula, old, t.markup(formula))
        _remove(script)


_VARIABLE = rf"(?:{_GREEK_CLASS}?[A-Za-z]|{_GREEK_CLASS})"
_VALUE = rf"(?:{_NUMBER}(?:\s?%)?|[A-Za-z]|{_GREEK_CLASS})"
_RELATION_TEXT = re.compile(
    rf"(?<![\w\-./Ͱ-Ͽ])(?P<lhs>{_VARIABLE})\s*(?P<op>{_RELATION})\s*(?P<rhs>{_VALUE})(?![\wͰ-Ͽ]|[.,]\d)"
)
_RELATION_AFTER_FORMULA = re.compile(rf"^\s*(?P<op>{_RELATION})\s*(?P<rhs>{_VALUE})(?![\wͰ-Ͽ]|[.,]\d)")


def _value_latex(value: str) -> str:
    value = value.replace(" %", "%").replace("%", r"\%")
    return to_latex(_number_latex(value)) if re.match(r"[-−\d]", value) else to_latex(value)


def relation(ctx: Context) -> None:
    def convert(slot: t.Slot, match: re.Match[str]) -> t.Slot | None:
        latex = f"{to_latex(match.group('lhs'))} {to_latex(match.group('op'))} {_value_latex(match.group('rhs'))}"
        formula = t.wrap_span(slot, match.start(), match.end(), "formula", latex)
        ctx.record(formula, match.group(), t.markup(formula))
        return (formula, "tail")

    _for_each_match(ctx, _RELATION_TEXT, t.FORMULA_HOSTS, convert, skip_greek_language=True)

    for formula in _formulas(ctx):  # a formula followed by the rest of its relation: <formula>x</formula> = 5
        if _inline_formula_text(formula) is None:
            continue
        match = _RELATION_AFTER_FORMULA.match(formula.tail or "")
        if match:
            old = t.markup(formula) + match.group()
            formula.text = f"{formula.text or ''} {to_latex(match.group('op'))} {_value_latex(match.group('rhs'))}"
            formula.tail = (formula.tail or "")[match.end() :] or None
            ctx.record(formula, old, t.markup(formula))


_LONE_GREEK = re.compile(rf"(?<![\w\-Ͱ-Ͽ])(?P<var>{_GREEK_CLASS})(?![\w\-Ͱ-Ͽ])")
_LONE_LATIN = re.compile(
    r"\b(?i:where|let|for all|for each|for any|for every|for small|for large|for|if)\s+(?P<var>[B-HJ-Zb-z])"
    r"(?=\s+(?:is|are|be|denotes|represents|stands|equals)\b|\s*[,.;:)]|\s*$)"
)


def lone_variable(ctx: Context) -> None:
    for italic in [e for e in t.iter_named(ctx.root, "italic") if t.in_prose(e)]:
        parent = italic.getparent()
        text = t.plain_text(italic)
        if parent is None or t.name(parent) not in t.FORMULA_HOSTS or text is None:
            continue
        if not re.fullmatch(rf"(?:[A-Za-z]|{_GREEK_CLASS})['′]*", text.strip()):
            continue
        before, after = t.get(t.before(italic)), italic.tail or ""
        if before[-1:].isalnum() or after[:1].isalnum() or re.search(r"\d\s*$", before):
            continue  # glued to a word, or a panel label: Fig. 1a, 2 a
        if before.rstrip().endswith("(") and after.lstrip().startswith(")"):
            continue  # an enumeration label: (a)
        latex = to_latex(text.strip().replace("′", "'"))
        formula = _insert_formula_before(italic, latex)
        ctx.record(formula, t.markup(italic), t.markup(formula))
        _remove(italic)

    def convert(slot: t.Slot, match: re.Match[str]) -> t.Slot | None:
        text = t.get(slot)
        if match.group("var") in "μµΩ" and _ENDS_WITH_DIGIT.search(text[: match.start("var")]):
            return None  # a unit after a number
        formula = t.wrap_span(slot, match.start("var"), match.end("var"), "formula", to_latex(match.group("var")))
        ctx.record(formula, match.group("var"), t.markup(formula))
        return (formula, "tail")

    _for_each_match(ctx, _LONE_GREEK, t.FORMULA_HOSTS, convert, skip_greek_language=True)
    _for_each_match(ctx, _LONE_LATIN, t.FORMULA_HOSTS, convert, skip_greek_language=True)


# --------------------------------------------------------------------------------------------------------------
# the rules, in the order they run; the merges run last so that they also join what tier 2 rules made

RULES: tuple[Rule, ...] = (
    Rule("celsius-fahrenheit", 1, "℃ and ℉ become °C and °F", celsius_fahrenheit),
    Rule(
        "unicode-script",
        1,
        "Unicode super/subscript characters in text become <superscript>/<subscript>",
        unicode_scripts,
    ),
    Rule(
        "formula-formatting", 1, "formatting inside a formula becomes LaTeX (^{}, _{}, \\mathbf{})", formula_formatting
    ),
    Rule("formula-unicode", 1, "Unicode math inside a formula becomes LaTeX (α → \\alpha, ² → ^{2})", formula_unicode),
    Rule("trademark", 1, "™ ® © written as a superscript or a formula become the character", trademark),
    Rule("degree", 1, "degree signs written as formulas, superscripts or look-alike characters become °", degree),
    Rule("ordinal-formula", 1, "an ordinal suffix written as a formula (^{th}) becomes <superscript>", ordinal_formula),
    Rule("scientific-notation", 1, "3 × 10<superscript>-5</superscript> becomes one formula", scientific_notation),
    Rule(
        "degree-ambiguous",
        2,
        "o raised after a number (90<superscript>o</superscript>, 37 o C) becomes °",
        degree_ambiguous,
    ),
    Rule(
        "greek-name-or-unit",
        2,
        "a Greek letter formula glued to a name or unit (α-helix, 5 μm) becomes text",
        greek_name_or_unit,
    ),
    Rule(
        "label-noise",
        2,
        "a single raised letter that completes the next word (<superscript>w</superscript>here) becomes text",
        label_noise,
    ),
    Rule("power-of-ten", 2, "10<superscript>-5</superscript> on its own becomes a formula", power_of_ten),
    Rule(
        "script-variable", 2, "a single-letter variable with a script (x², σ₁, Iₙ) becomes a formula", script_variable
    ),
    Rule("relation", 2, "a simple relation (x = 5, p < 0.05, σ = 0.3) becomes a formula", relation),
    Rule(
        "lone-variable",
        2,
        "a lone variable (italic x, a standalone Greek letter, 'where x is') becomes a formula",
        lone_variable,
    ),
    Rule(
        "formula-script-merge",
        1,
        "a formula followed by <superscript>/<subscript> becomes one formula",
        formula_script_merge,
    ),
    Rule("formula-merge", 1, "formulas separated only by whitespace or an operator become one formula", formula_merge),
)

RULE_IDS = tuple(rule.id for rule in RULES)
