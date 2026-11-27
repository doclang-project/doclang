# ruff: noqa: RUF001  # Unicode math and Greek letters are the subject matter
"""Tests for the normalization of super/subscripts, symbols and inline math (``doclang.normalize``)."""

from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest
from lxml import etree
from typer.testing import CliRunner

from doclang import NormalizationError, normalize
from doclang.cli import app
from doclang.normalization import rules
from doclang.normalization._api import normalize_tree
from doclang.normalization._latex import to_latex

NS = "https://www.doclang.ai/ns/v0"
runner = CliRunner()


def _doc(body: str, *, element: str = "text") -> str:
    return f'<doclang xmlns="{NS}" version="0.9"><{element}>{body}</{element}></doclang>'


def _normalize_body(body: str, tier: int = 1, only: list[str] | None = None) -> tuple[str, list[dict], list[dict]]:
    root = etree.fromstring(_doc(body))
    changes, suggestions = normalize_tree(root, tier=tier, only=only)
    inner = etree.tostring(root[0], encoding="unicode").replace(f' xmlns="{NS}"', "")
    return inner[len("<text>") : -len("</text>")], changes, suggestions


TIER_1 = [
    # temperature, trademark and degree symbols
    ("at 37℃ or 99℉", "at 37°C or 99°F"),
    ("Teflon<superscript>TM</superscript> and Brand<formula>^{TM}</formula>", "Teflon™ and Brand™"),
    ("Acme<formula>\\textregistered</formula>", "Acme®"),
    ("angle of 90<formula>^{\\circ}</formula>", "angle of 90°"),
    ("<formula>37^{\\circ}\\mathrm{C}</formula> warm", "37°C warm"),
    ("<formula>{ }^{\\circ} \\mathrm{C}</formula>", "°C"),
    ("20 <superscript>o</superscript>C", "20 °C"),
    ("20<superscript>0</superscript>C", "20°C"),
    ("rotated 45<superscript>∘</superscript>", "rotated 45°"),
    ("at 37 ◦C and 5˚ and 4ºC", "at 37 °C and 5° and 4°C"),
    # ordinals
    ("the 30<formula>^{th}</formula> day", "the 30<superscript>th</superscript> day"),
    ("the <formula>30^{\\text{th}}</formula> day", "the 30<superscript>th</superscript> day"),
    ("2ⁿᵈ place", "2<superscript>nd</superscript> place"),
    # Unicode scripts become tags; modifier letters outside numbers stay (phonetics)
    (
        "H₂O, CO₂, 5 km², Ca²⁺",
        "H<subscript>2</subscript>O, CO<subscript>2</subscript>, 5 km<superscript>2</superscript>, Ca<superscript>2+</superscript>",
    ),
    ("cm⁻¹", "cm<superscript>-1</superscript>"),
    ("the kʰ sound", "the kʰ sound"),
    ("<bold>CO₂</bold>", "<bold>CO<subscript>2</subscript></bold>"),
    # scientific notation
    ("a rate of 3 × 10<superscript>-5</superscript> M", "a rate of <formula>3 \\times 10^{-5}</formula> M"),
    ("1,5 x 10<superscript>−3</superscript>", "<formula>1{,}5 \\times 10^{-3}</formula>"),
    ("4.2 × 10⁻⁵ M", "<formula>4.2 \\times 10^{-5}</formula> M"),
    # formulas: Unicode and formatting inside, splits
    ("<formula>∠ABC = 90°</formula>", "<formula>\\angle ABC = 90^{\\circ}</formula>"),
    ("<formula>αx + β²</formula>", "<formula>\\alpha x + \\beta^{2}</formula>"),
    ("<formula>√(x+1) ≤ 2</formula>", "<formula>\\sqrt{x+1} \\leq 2</formula>"),
    (
        "<formula>x<superscript>2</superscript> + y<subscript>i</subscript></formula>",
        "<formula>x^{2} + y_{i}</formula>",
    ),
    ("<formula>2x</formula><superscript>2</superscript> grows", "<formula>2x^{2}</formula> grows"),
    ("<formula>x^{2}</formula><superscript>3</superscript>", "<formula>{x^{2}}^{3}</formula>"),
    ("<formula>x</formula><subscript>i</subscript><superscript>2</superscript>", "<formula>x_{i}^{2}</formula>"),
    ("<formula>a</formula> = <formula>b</formula>", "<formula>a = b</formula>"),
    ("<formula>a</formula> × <formula>b</formula> = <formula>c</formula>", "<formula>a \\times b = c</formula>"),
    # left alone
    ("<formula>a</formula>, <formula>b</formula>", "<formula>a</formula>, <formula>b</formula>"),
    ("<formula>x</formula>–<formula>y</formula> plane", "<formula>x</formula>–<formula>y</formula> plane"),
    ("x<superscript>2</superscript>", "x<superscript>2</superscript>"),  # tier 2
    ("word<superscript>1</superscript>", "word<superscript>1</superscript>"),
    ("1<superscript>st</superscript> question", "1<superscript>st</superscript> question"),
    ("90<superscript>o</superscript> angle", "90<superscript>o</superscript> angle"),  # tier 2
    ("<formula>\\angle ABC = 90^{\\circ}</formula>", "<formula>\\angle ABC = 90^{\\circ}</formula>"),
    ("20 °C ± 5 °C", "20 °C ± 5 °C"),
]


@pytest.mark.parametrize(("body", "expected"), TIER_1)
def test_tier_1(body, expected):
    assert _normalize_body(body)[0] == expected


TIER_2 = [
    # variables with scripts
    ("the variable x<superscript>2</superscript>, then", "the variable <formula>x^{2}</formula>, then"),
    (
        "I<subscript>n</subscript> and σ<subscript>1</subscript>",
        "<formula>I_{n}</formula> and <formula>\\sigma_{1}</formula>",
    ),
    ("R² = 0.9", "<formula>R^{2} = 0.9</formula>"),
    ("x² + y² = r²", "<formula>x^{2} + y^{2} = r^{2}</formula>"),
    ("<italic>x</italic><superscript>2</superscript>", "<formula>x^{2}</formula>"),
    # ... but not chemistry, units, isotopes, reference marks or initials
    ("O<subscript>2</subscript> levels", "O<subscript>2</subscript> levels"),
    ("H<subscript>2</subscript>O", "H<subscript>2</subscript>O"),
    ("Ca<superscript>2+</superscript>", "Ca<superscript>2+</superscript>"),
    ("5 m<superscript>2</superscript>", "5 m<superscript>2</superscript>"),
    ("1000 kg m<superscript>-3</superscript>", "1000 kg m<superscript>-3</superscript>"),
    ("in m/s<superscript>2</superscript>", "in m/s<superscript>2</superscript>"),
    ("<superscript>13</superscript>C", "<superscript>13</superscript>C"),
    ("Smith J<superscript>1</superscript>, Doe", "Smith J<superscript>1</superscript>, Doe"),
    ("shown<superscript>12</superscript>.", "shown<superscript>12</superscript>."),
    ("2.71<superscript>bF</superscript>", "2.71<superscript>bF</superscript>"),
    # powers of ten, degrees
    ("about 10<superscript>6</superscript> cells", "about <formula>10^{6}</formula> cells"),
    ("rotated 90<superscript>o</superscript> clockwise", "rotated 90° clockwise"),
    ("at 37 o C", "at 37 °C"),
    # relations and lone variables
    ("p &lt; 0.05 and n = 12 subjects", "<formula>p &lt; 0.05</formula> and <formula>n = 12</formula> subjects"),
    ("σ = 0.3, ΔG = 5", "<formula>\\sigma = 0.3</formula>, <formula>\\Delta G = 5</formula>"),
    ("<formula>x</formula> = 5 cm", "<formula>x = 5</formula> cm"),
    ("For small x, it holds", "For small <formula>x</formula>, it holds"),
    ("where n is the size", "where <formula>n</formula> is the size"),
    ("the parameter α is", "the parameter <formula>\\alpha</formula> is"),
    ("and <italic>y</italic> and <italic>θ′</italic>", "and <formula>y</formula> and <formula>\\theta'</formula>"),
    # ... but not names, units, labels, Greek text
    ("the α-helix, 5 μm, PDGFRβ and β-carotene", "the α-helix, 5 μm, PDGFRβ and β-carotene"),
    ("Fig. 1<italic>a</italic> and (<italic>b</italic>)", "Fig. 1<italic>a</italic> and (<italic>b</italic>)"),
    ("Η τιμή α = 3 είναι", "Η τιμή α = 3 είναι"),
    ("for a while", "for a while"),
    ("x-axis and y = mx", "x-axis and y = mx"),
    # lone formulas that are names or units become text
    ("<formula>\\alpha</formula>-helix", "α-helix"),
    ("10 <formula>\\mu</formula>m", "10 μm"),
    ("PDGFR<formula>\\beta</formula>", "PDGFRβ"),
    # label noise
    ("found <superscript>w</superscript>here it", "found where it"),
]


@pytest.mark.parametrize(("body", "expected"), TIER_2)
def test_tier_2(body, expected):
    assert _normalize_body(body, tier=2)[0] == expected


def test_tier_1_reports_tier_2_suggestions_without_applying_them():
    out, changes, suggestions = _normalize_body("H₂O and x<superscript>2</superscript>")
    assert out == "H<subscript>2</subscript>O and x<superscript>2</superscript>"
    assert [c["rule"] for c in changes] == ["unicode-script"]
    assert [(s["rule"], s["kind"], s["tier"]) for s in suggestions] == [("script-variable", "suggested", 2)]
    assert changes[0]["kind"] == "fixed"
    assert changes[0]["location"] == "/doclang/text"
    assert changes[0]["message"] == "₂ → <subscript>2</subscript>"


def test_only_selected_rules_run():
    out, changes, _ = _normalize_body("37℃ and H₂O", only=["celsius-fahrenheit"])
    assert out == "37°C and H₂O"
    assert [c["rule"] for c in changes] == ["celsius-fahrenheit"]
    with pytest.raises(ValueError, match="unknown rule"):
        _normalize_body("x", only=["nope"])


def test_rules_are_listed_with_their_tier():
    listed = {r["id"]: r["tier"] for r in rules()}
    assert listed["degree"] == 1 and listed["script-variable"] == 2
    assert len(listed) == len(rules())


@pytest.mark.parametrize(
    ("latex", "expected"),
    [
        ("x² + αβ", "x^{2} + \\alpha\\beta"),
        ("x₁₂ ⋅ y⁻¹", "x_{12} \\cdot y^{-1}"),
        ("a ≠ b → c", "a \\neq b \\rightarrow c"),
        ("\\frac{a}{b}", "\\frac{a}{b}"),
        ("µm", "\\mu m"),
    ],
)
def test_to_latex(latex, expected):
    assert to_latex(latex) == expected


def test_block_formulas_and_formulas_with_a_head_are_not_turned_into_text_or_merged():
    xml = (
        f'<doclang xmlns="{NS}" version="0.9"><formula>^{{TM}}</formula>'
        '<text><formula><location value="1"/><location value="2"/><location value="3"/><location value="4"/>a'
        "</formula> = <formula>b</formula></text></doclang>"
    )
    root = etree.fromstring(xml)
    normalize_tree(root, tier=2)
    assert etree.tostring(root, encoding="unicode") == xml


def test_formula_content_keeps_cdata():
    xml = (
        f'<doclang xmlns="{NS}" version="0.9"><formula><content><![CDATA[a &= α \\\\ b]]></content></formula></doclang>'
    )
    root = etree.fromstring(xml, parser=etree.XMLParser(strip_cdata=False))
    normalize_tree(root)
    assert "<![CDATA[a &= \\alpha \\\\ b]]>" in etree.tostring(root, encoding="unicode")


def test_scripts_in_hosts_that_allow_no_elements_stay():
    xml = f'<doclang xmlns="{NS}" version="0.9"><picture><description>CO₂ at 37℃</description></picture></doclang>'
    root = etree.fromstring(xml)
    normalize_tree(root, tier=2)
    assert "<description>CO₂ at 37°C</description>" in etree.tostring(root, encoding="unicode")


def test_document_without_namespace(tmp_path):
    doc = tmp_path / "plain.dclg"
    doc.write_text('<doclang version="0.9"><text>H₂O and x<superscript>2</superscript></text></doclang>\n', "utf-8")
    result = normalize(doc, tier=2, input_validation="xsd", output_validation="xsd")
    assert "<formula>x^{2}</formula>" in result.xml and "ns0" not in result.xml


COMPREHENSIVE = f"""<?xml version="1.0" encoding="UTF-8"?>
<doclang xmlns="{NS}" version="0.9">
  <heading>Effect of CO₂ at 37℃</heading>
  <text>
    We measured x² and <formula>2x</formula><superscript>2</superscript> with p &lt; 0.05,
    where τ<subscript>x,y,z</subscript> are the Pauli matrices and the angle θ is 90<formula>^{{\\circ}}</formula>.
  </text>
  <list>
    <ldiv/>Teflon<superscript>TM</superscript> in 5 km²
    <ldiv/>about 3 × 10⁻⁵ M of H₂O
  </list>
  <table>
    <fcel/>σ = 0.3<fcel/>2.71ᵇᶠ<nl/>
    <fcel/>Ca²⁺<fcel/><italic>x</italic><superscript>2</superscript><nl/>
  </table>
  <picture>
    <caption>FIG. 1. The α-helix at 20 <superscript>o</superscript>C</caption>
  </picture>
  <formula>∑ᵢ xᵢ² ≤ ∞</formula>
</doclang>
"""


@pytest.mark.parametrize("tier", [1, 2])
def test_normalized_document_is_valid(tmp_path, tier):
    doc = tmp_path / "doc.dclg"
    doc.write_text(COMPREHENSIVE, "utf-8")
    result = normalize(doc, tier=tier, input_validation="xsd", output_validation="xsd")
    assert result.xml.startswith('<?xml version="1.0" encoding="UTF-8"?>\n')
    assert "37°C" in result.xml and "™" in result.xml and "\\sum_{i} x_{i}^{2} \\leq \\infty" in result.xml
    if tier == 2:
        assert "<formula>\\tau_{x,y,z}</formula>" in result.xml
        assert "<formula>\\theta</formula> is 90°" in result.xml
        assert not result.suggestions
    else:
        assert result.suggestions


def test_already_normalized_document_has_no_changes(tmp_path):
    doc = tmp_path / "doc.dclg"
    doc.write_text(COMPREHENSIVE, "utf-8")
    once = tmp_path / "once.dclg"
    normalize(doc, tier=2, output=once, input_validation="xsd", output_validation="xsd")
    again = normalize(once, tier=2, input_validation="xsd", output_validation="xsd")
    assert again.changes == []
    assert again.xml == once.read_text("utf-8")


def test_valid_fixtures_stay_valid():
    for path in sorted(Path("tests/data/valid").glob("*.dclg")):
        try:
            normalize(path, tier=2, input_validation="xsd", output_validation="xsd")
        except NormalizationError as exc:
            assert "fix it before normalizing" in str(exc), f"{path}: {exc}"


def test_invalid_input_is_an_error(tmp_path):
    doc = tmp_path / "bad.dclg"
    doc.write_text(f'<doclang xmlns="{NS}" version="0.9"><bogus/></doclang>', "utf-8")
    with pytest.raises(NormalizationError, match="not valid"):
        normalize(doc, input_validation="xsd", output_validation="xsd")


def test_archive(tmp_path):
    archive = tmp_path / "doc.dclx"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("document.xml", _doc("37℃"))
        zf.writestr("assets/a.txt", "keep")
    out = tmp_path / "out.dclx"
    normalize(archive, output=out, input_validation="xsd", output_validation="xsd")
    with zipfile.ZipFile(out) as zf:
        assert "37°C" in zf.read("document.xml").decode()
        assert zf.read("assets/a.txt") == b"keep"


def test_cli_writes_document_and_reports_changes(tmp_path):
    doc = tmp_path / "doc.dclg"
    doc.write_text(_doc("H₂O and x<superscript>2</superscript>"), "utf-8")
    args = ["normalize", str(doc), "--input-validation", "xsd", "--output-validation", "xsd"]
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert "H<subscript>2</subscript>O" in result.stdout
    assert "Fixed [unicode-script]" in result.stderr
    assert "Suggested [script-variable]" in result.stderr

    result = runner.invoke(app, [*args, "--tier", "2", "--format", "json"])
    payload = json.loads(result.stdout)
    assert [c["rule"] for c in payload["changes"]] == ["unicode-script", "script-variable"]
    assert "<formula>x^{2}</formula>" in payload["xml"]


def test_cli_check_and_in_place(tmp_path):
    doc = tmp_path / "doc.dclg"
    doc.write_text(_doc("37℃"), "utf-8")
    args = ["--input-validation", "xsd", "--output-validation", "xsd"]
    assert runner.invoke(app, ["normalize", str(doc), "--check", *args]).exit_code == 1
    assert "℃" in doc.read_text("utf-8")
    assert runner.invoke(app, ["normalize", str(doc), "-i", *args]).exit_code == 0
    assert "37°C" in doc.read_text("utf-8")
    assert runner.invoke(app, ["normalize", str(doc), "--check", *args]).exit_code == 0


def test_cli_lists_rules():
    result = runner.invoke(app, ["normalize", "--list-rules"])
    assert result.exit_code == 0
    assert "script-variable" in result.stdout and "tier 2" in result.stdout
