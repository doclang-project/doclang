# ruff: noqa: RUF001, RUF002  # Unicode math and Greek letters are the subject matter
"""Character tables for math normalization: Unicode scripts, Greek letters and math symbols (internal)."""

from __future__ import annotations

import re

# Unicode superscript characters and what they raise.
SUPERSCRIPTS: dict[str, str] = {
    "⁰": "0",
    "¹": "1",
    "²": "2",
    "³": "3",
    "⁴": "4",
    "⁵": "5",
    "⁶": "6",
    "⁷": "7",
    "⁸": "8",
    "⁹": "9",
    "⁺": "+",
    "⁻": "-",
    "⁼": "=",
    "⁽": "(",
    "⁾": ")",
    "ⁿ": "n",
    "ⁱ": "i",
}

# Modifier letters: also used in phonetic transcription (kʰ), so only taken as superscripts after a digit.
SUPERSCRIPT_LETTERS: dict[str, str] = {
    "ᵃ": "a",
    "ᵇ": "b",
    "ᶜ": "c",
    "ᵈ": "d",
    "ᵉ": "e",
    "ᶠ": "f",
    "ᵍ": "g",
    "ʰ": "h",
    "ʲ": "j",
    "ᵏ": "k",
    "ˡ": "l",
    "ᵐ": "m",
    "ᵒ": "o",
    "ᵖ": "p",
    "ʳ": "r",
    "ˢ": "s",
    "ᵗ": "t",
    "ᵘ": "u",
    "ᵛ": "v",
    "ʷ": "w",
    "ˣ": "x",
    "ʸ": "y",
    "ᶻ": "z",
    "ᴬ": "A",
    "ᴮ": "B",
    "ᴰ": "D",
    "ᴱ": "E",
    "ᴳ": "G",
    "ᴴ": "H",
    "ᴵ": "I",
    "ᴶ": "J",
    "ᴷ": "K",
    "ᴸ": "L",
    "ᴹ": "M",
    "ᴺ": "N",
    "ᴼ": "O",
    "ᴾ": "P",
    "ᴿ": "R",
    "ᵀ": "T",
    "ᵁ": "U",
    "ⱽ": "V",
    "ᵂ": "W",
}

SUBSCRIPTS: dict[str, str] = {
    "₀": "0",
    "₁": "1",
    "₂": "2",
    "₃": "3",
    "₄": "4",
    "₅": "5",
    "₆": "6",
    "₇": "7",
    "₈": "8",
    "₉": "9",
    "₊": "+",
    "₋": "-",
    "₌": "=",
    "₍": "(",
    "₎": ")",
    "ₐ": "a",
    "ₑ": "e",
    "ₒ": "o",
    "ₓ": "x",
    "ₕ": "h",
    "ₖ": "k",
    "ₗ": "l",
    "ₘ": "m",
    "ₙ": "n",
    "ₚ": "p",
    "ₛ": "s",
    "ₜ": "t",
    "ᵢ": "i",
    "ⱼ": "j",
    "ᵣ": "r",
    "ᵤ": "u",
    "ᵥ": "v",
}

ALL_SUPERSCRIPTS = {**SUPERSCRIPTS, **SUPERSCRIPT_LETTERS}

GREEK: dict[str, str] = {
    "α": r"\alpha",
    "β": r"\beta",
    "γ": r"\gamma",
    "δ": r"\delta",
    "ε": r"\varepsilon",
    "ϵ": r"\epsilon",
    "ζ": r"\zeta",
    "η": r"\eta",
    "θ": r"\theta",
    "ϑ": r"\vartheta",
    "ι": r"\iota",
    "κ": r"\kappa",
    "λ": r"\lambda",
    "μ": r"\mu",
    "ν": r"\nu",
    "ξ": r"\xi",
    "π": r"\pi",
    "ϖ": r"\varpi",
    "ρ": r"\rho",
    "ϱ": r"\varrho",
    "σ": r"\sigma",
    "ς": r"\varsigma",
    "τ": r"\tau",
    "υ": r"\upsilon",
    "φ": r"\varphi",
    "ϕ": r"\phi",
    "χ": r"\chi",
    "ψ": r"\psi",
    "ω": r"\omega",
    "Γ": r"\Gamma",
    "Δ": r"\Delta",
    "Θ": r"\Theta",
    "Λ": r"\Lambda",
    "Ξ": r"\Xi",
    "Π": r"\Pi",
    "Σ": r"\Sigma",
    "Υ": r"\Upsilon",
    "Φ": r"\Phi",
    "Ψ": r"\Psi",
    "Ω": r"\Omega",
}

# Greek capitals without a LaTeX command of their own, and look-alikes of Greek letters.
_GREEK_EXTRA: dict[str, str] = {
    "Α": "A",
    "Β": "B",
    "Ε": "E",
    "Ζ": "Z",
    "Η": "H",
    "Ι": "I",
    "Κ": "K",
    "Μ": "M",
    "Ν": "N",
    "Ο": "O",
    "Ρ": "P",
    "Τ": "T",
    "Χ": "X",
    "ο": "o",
    "µ": r"\mu",  # micro sign
    "Ω": r"\Omega",  # ohm sign
    "∆": r"\Delta",  # increment
}

# LaTeX command of a Greek letter -> the Unicode letter, for turning lone formulas back into text.
GREEK_FROM_LATEX: dict[str, str] = {latex: char for char, latex in GREEK.items()}
GREEK_FROM_LATEX[r"\epsilon"] = "ε"
GREEK_FROM_LATEX[r"\phi"] = "φ"

GREEK_LETTERS = "".join(GREEK) + "µ"

SYMBOLS: dict[str, str] = {
    "×": r"\times",
    "·": r"\cdot",
    "⋅": r"\cdot",
    "÷": r"\div",
    "±": r"\pm",
    "∓": r"\mp",
    "−": "-",
    "–": "-",
    "≤": r"\leq",
    "≦": r"\leq",
    "≥": r"\geq",
    "≧": r"\geq",
    "≠": r"\neq",
    "≈": r"\approx",
    "≡": r"\equiv",
    "∼": r"\sim",
    "≃": r"\simeq",
    "≅": r"\cong",
    "∝": r"\propto",
    "≪": r"\ll",
    "≫": r"\gg",
    "∞": r"\infty",
    "→": r"\rightarrow",
    "←": r"\leftarrow",
    "↔": r"\leftrightarrow",
    "⇒": r"\Rightarrow",
    "⇐": r"\Leftarrow",
    "⇔": r"\Leftrightarrow",
    "↦": r"\mapsto",
    "⇌": r"\rightleftharpoons",
    "∈": r"\in",
    "∉": r"\notin",
    "∋": r"\ni",
    "⊂": r"\subset",
    "⊃": r"\supset",
    "⊆": r"\subseteq",
    "⊇": r"\supseteq",
    "∪": r"\cup",
    "∩": r"\cap",
    "∖": r"\setminus",
    "∅": r"\emptyset",
    "∀": r"\forall",
    "∃": r"\exists",
    "¬": r"\neg",
    "∧": r"\wedge",
    "∨": r"\vee",
    "⊕": r"\oplus",
    "⊗": r"\otimes",
    "∘": r"\circ",
    "•": r"\bullet",
    "∗": "*",
    "∑": r"\sum",
    "∏": r"\prod",
    "∫": r"\int",
    "∬": r"\iint",
    "∮": r"\oint",
    "∂": r"\partial",
    "∇": r"\nabla",
    "√": r"\sqrt",
    "∠": r"\angle",
    "⊥": r"\perp",
    "∥": r"\parallel",
    "‖": r"\|",
    "°": r"^{\circ}",
    "℃": r"^{\circ}\mathrm{C}",
    "℉": r"^{\circ}\mathrm{F}",
    "′": "'",
    "″": "''",
    "…": r"\ldots",
    "⋯": r"\cdots",
    "ℏ": r"\hbar",
    "ℓ": r"\ell",
    "ℝ": r"\mathbb{R}",
    "ℕ": r"\mathbb{N}",
    "ℤ": r"\mathbb{Z}",
    "ℚ": r"\mathbb{Q}",
    "ℂ": r"\mathbb{C}",
    "⟨": r"\langle",
    "⟩": r"\rangle",
    "⁄": "/",
    "Å": r"\mathring{A}",
}

TO_LATEX: dict[str, str] = {**GREEK, **_GREEK_EXTRA, **SYMBOLS}

_SUP_RUN = re.compile("[" + "".join(ALL_SUPERSCRIPTS) + "]+")
_SUB_RUN = re.compile("[" + "".join(SUBSCRIPTS) + "]+")
_ASCII_LETTER = re.compile(r"[A-Za-z]")


def needs_latex(text: str) -> bool:
    """Whether ``text`` (formula content) has characters that :func:`to_latex` would rewrite."""
    return any(c in TO_LATEX or c in ALL_SUPERSCRIPTS or c in SUBSCRIPTS for c in text)


def script_text(text: str) -> str:
    """The LaTeX for the content of a script, e.g. ``-1`` for ``−1`` or ``\\alpha`` for ``α``."""
    return to_latex(text).strip()


def to_latex(text: str) -> str:
    """Rewrite the Unicode math in ``text`` (formula content) as LaTeX; other characters are kept.

    Runs of superscript or subscript characters become one script (``x²³`` → ``x^{23}``), and a command that
    ends in a letter is separated from a following letter (``αx`` → ``\\alpha x``).
    """
    out: list[str] = []
    i = 0
    while i < len(text):
        char = text[i]
        if char in ALL_SUPERSCRIPTS:
            run = _SUP_RUN.match(text, i)
            assert run is not None
            _append(out, "^{" + "".join(ALL_SUPERSCRIPTS[c] for c in run.group()) + "}")
            i = run.end()
            continue
        if char in SUBSCRIPTS:
            run = _SUB_RUN.match(text, i)
            assert run is not None
            _append(out, "_{" + "".join(SUBSCRIPTS[c] for c in run.group()) + "}")
            i = run.end()
            continue
        if char == "√" and text[i + 1 : i + 2] == "(":
            close = _matching_paren(text, i + 1)
            if close is not None:
                _append(out, r"\sqrt{" + to_latex(text[i + 2 : close]) + "}")
                i = close + 1
                continue
        _append(out, TO_LATEX.get(char, char))
        i += 1
    return "".join(out)


def _append(out: list[str], piece: str) -> None:
    """Append ``piece``, separating it from a preceding command that would otherwise swallow its letters."""
    if out and _ASCII_LETTER.match(piece) and re.search(r"\\[A-Za-z]+$", out[-1]):
        out.append(" ")
    out.append(piece)


def _matching_paren(text: str, start: int) -> int | None:
    depth = 0
    for j in range(start, len(text)):
        if text[j] == "(":
            depth += 1
        elif text[j] == ")":
            depth -= 1
            if depth == 0:
                return j
    return None
