"""Targeted coverage for every native Schematron assertion."""

from pathlib import Path
from xml.etree import ElementTree

import pytest

from doclang import DoclangDocument, DocLangXDocument, ValidationError, validate_document
from doclang._native import _schematron_errors_xml

_NAMESPACE = 'xmlns="https://www.doclang.ai/ns/v0"'
_VALID_DIR = Path(__file__).parent / "data" / "valid"
_SCHEMA = Path(__file__).parent.parent / "doclang" / "doclang.sch"
pytestmark = pytest.mark.validation


def _xml(body):
    return f"<doclang {_NAMESPACE}>{body}</doclang>"


_ASSERTIONS = [
    ("list-structure", "<list><ldiv/></list>", "<list><text/><ldiv/></list>"),
    ("table-structure", "<table><fcel/></table>", "<table><nl/></table>"),
    (
        "table-rectangular-grid",
        "<table><fcel/><lcel/><nl/><fcel/><lcel/><nl/></table>",
        "<table><fcel/><lcel/><nl/><fcel/><nl/></table>",
    ),
    ("element-head-placement", "<text><label/>Body</text>", "<text>Body<label/></text>"),
    (
        "xref-href-mutual-exclusivity",
        '<text><xref thread_id="1"/></text><text><thread thread_id="1"/></text>',
        '<text><xref thread_id="1"/><href uri="https://example.org"/></text><text><thread thread_id="1"/></text>',
    ),
    (
        "xref-thread-defined",
        '<text><xref thread_id="1"/></text><text><thread thread_id="1"/></text>',
        '<text><xref thread_id="1"/></text>',
    ),
    (
        "location-value-range",
        '<text><location value="0" resolution="10"/><location value="0"/>'
        '<location value="9" resolution="10"/><location value="9"/></text>',
        '<text><location value="10" resolution="10"/><location value="0"/>'
        '<location value="9" resolution="10"/><location value="9"/></text>',
    ),
    (
        "location-block-order",
        '<text><location value="10"/><location value="10"/><location value="50"/><location value="50"/></text>',
        '<text><location value="100"/><location value="10"/><location value="50"/><location value="50"/></text>',
    ),
    (
        "thread-host-type-consistency",
        '<text><thread thread_id="1"/></text><text><thread thread_id="1"/></text>',
        '<text><thread thread_id="1"/></text><picture><thread thread_id="1"/></picture>',
    ),
    (
        "list-virtual-text-element-head",
        "<list><ldiv/><label/>Body</list>",
        "<list><ldiv/>Body<label/></list>",
    ),
    (
        "table-virtual-text-element-head",
        "<table><fcel/><label/>Body</table>",
        "<table><fcel/>Body<label/></table>",
    ),
    ("field-heading-region", "<field_region><field_heading/></field_region>", "<field_heading/>"),
    ("field-item-region", "<field_region><field_item/></field_region>", "<field_item/>"),
    ("key-field-item", "<field_region><field_item><key/></field_item></field_region>", "<key/>"),
    ("value-field-item", "<field_region><field_item><value/></field_item></field_region>", "<value/>"),
    (
        "field-item-own-key",
        "<field_region><field_item><key/></field_item></field_region>",
        "<field_region><field_item><key/><key/></field_item></field_region>",
    ),
    (
        "picture-tabular-chart",
        '<picture class="chart"><tabular/></picture>',
        "<picture><tabular/></picture>",
    ),
    (
        "picture-src-first",
        "<picture><src/></picture>",
        "<picture><text/><src/></picture>",
    ),
    (
        "picture-tabular-after-src",
        '<picture class="chart"><src/><tabular/></picture>',
        '<picture class="chart"><src/><text/><tabular/></picture>',
    ),
]


def test_native_matrix_covers_every_schema_assertion():
    schema = ElementTree.parse(_SCHEMA)
    assertions = schema.findall(".//{http://purl.oclc.org/dsdl/schematron}assert")
    ids = [assertion.get("id") for assertion in assertions]
    assert len(ids) == len(set(ids)) == 19
    assert set(ids) == {assertion for assertion, _, _ in _ASSERTIONS}


@pytest.mark.parametrize(("assertion", "valid_body", "invalid_body"), _ASSERTIONS)
def test_native_assertion_has_passing_and_failing_case(assertion, valid_body, invalid_body):
    assert not any(issue["assertion"] == assertion for issue in _schematron_errors_xml(_xml(valid_body)))
    issues = _schematron_errors_xml(_xml(invalid_body))
    assert any(issue["assertion"] == assertion for issue in issues)
    assert all(issue["location"] and issue["message"] for issue in issues)


@pytest.mark.parametrize("path", sorted(_VALID_DIR.glob("*.dclg.xml")), ids=lambda path: path.stem)
def test_existing_valid_fixtures_pass_native_rules(path):
    allow_empty = path.stem in {"ok_no_namespace.dclg", "doclang_example.dclg"}
    assert _schematron_errors_xml(path.read_text(), allow_empty) == []


def test_native_rules_resolve_prefixed_and_optional_empty_namespaces():
    prefixed = '<dl:doclang xmlns:dl="https://www.doclang.ai/ns/v0"><dl:text>Body<dl:label/></dl:text></dl:doclang>'
    empty = "<doclang><text>Body<label/></text></doclang>"
    assert [issue["assertion"] for issue in _schematron_errors_xml(prefixed)] == ["element-head-placement"]
    assert _schematron_errors_xml(empty) == []
    assert [issue["assertion"] for issue in _schematron_errors_xml(empty, True)] == ["element-head-placement"]


@pytest.mark.parametrize("document_type", [DoclangDocument, DocLangXDocument])
def test_document_validation_is_explicit(document_type):
    doc = document_type(_xml("<text>Body<label/></text>")) if document_type is DoclangDocument else document_type()
    if document_type is DocLangXDocument:
        assert doc.read_xml(_xml("<text>Body<label/></text>"))
    assert doc.valid()
    assert [issue["assertion"] for issue in doc.schematron_errors()] == ["element-head-placement"]


@pytest.mark.parametrize("document_type", [DoclangDocument, DocLangXDocument])
def test_validate_document_checks_in_memory_xml(document_type):
    valid_xml = _xml("<text>Body</text>")
    invalid_xml = _xml('<heading level="0">Bad</heading><text><xref thread_id="1"/>Body</text>')
    if document_type is DoclangDocument:
        doc = document_type(valid_xml)
    else:
        doc = document_type()
        assert doc.read_xml(valid_xml)

    assert validate_document(doc) is None
    assert doc.read_xml(invalid_xml)
    with pytest.raises(ValidationError) as caught:
        validate_document(doc)
    assert caught.value.xsd_errors
    assert [issue["assertion"] for issue in caught.value.schematron_errors] == ["xref-thread-defined"]

    with pytest.raises(ValidationError) as caught:
        validate_document(doc, schematron_only=True)
    assert not caught.value.xsd_errors
    assert caught.value.schematron_errors

    with pytest.raises(ValidationError) as caught:
        validate_document(doc, xsd_only=True)
    assert caught.value.xsd_errors
    assert not caught.value.schematron_errors
