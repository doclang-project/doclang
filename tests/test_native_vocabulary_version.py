"""Native XML vocabulary and document version API."""

from pathlib import Path
from xml.etree import ElementTree

import pytest

from doclang import (
    AttributeName,
    DoclangDocument,
    DoclangNode,
    DoclangVersion,
    DoclangXDocument,
    ElementTag,
    OtslToken,
    attribute_name_from_string,
    element_tag_from_string,
    otsl_token_from_string,
    xml_name,
)


def test_vocabulary_covers_schema_elements_and_attributes():
    schema = ElementTree.parse(Path(__file__).resolve().parents[1] / "doclang" / "doclang.xsd")
    namespace = {"xs": "http://www.w3.org/2001/XMLSchema"}
    for element in schema.findall("xs:element", namespace):
        name = element.attrib["name"]
        assert xml_name(element_tag_from_string(name)) == name
    for attribute in schema.findall(".//xs:attribute", namespace):
        name = attribute.attrib["name"]
        assert xml_name(attribute_name_from_string(name)) == name

    assert element_tag_from_string("unknown") is None
    assert attribute_name_from_string("unknown") is None
    assert xml_name(ElementTag.table) == "table"
    assert xml_name(AttributeName.class_) == "class"


@pytest.mark.parametrize(
    ("short", "long"),
    [
        ("fc", "fcel"),
        ("ec", "ecel"),
        ("ch", "ched"),
        ("rh", "rhed"),
        ("co", "corn"),
        ("sr", "srow"),
        ("lc", "lcel"),
        ("uc", "ucel"),
        ("xc", "xcel"),
        ("nl", "nl"),
    ],
)
def test_otsl_short_names_round_trip(short, long):
    token = otsl_token_from_string(short)
    assert token == otsl_token_from_string(long)
    assert xml_name(token) == long
    assert xml_name(getattr(OtslToken, short)) == long


def test_versions_compare_numerically_and_dclx_inherits_the_api():
    older = DoclangDocument('<doclang version="0.9"/>')
    newer = DoclangDocument('<doclang version="0.10"/>')
    assert older.version() < newer.version()
    assert newer.version() >= DoclangVersion.parse("0.10")
    assert DoclangVersion(1, 0) > newer.version()
    assert str(newer.version()) == "0.10"
    assert DoclangDocument.empty().version() == DoclangVersion(0, 6)
    assert DoclangDocument("<doclang/>").version() == DoclangVersion(0, 6)
    assert DoclangDocument().version() is None

    archive = DoclangXDocument()
    assert archive.read_xml('<doclang version="1.2"/>')
    assert archive.version() == DoclangVersion(1, 2)
    assert archive.version() > older.version()


@pytest.mark.parametrize("value", ["", "0", "0.6.0", "a.b", "1.-1", "1.2x"])
def test_invalid_version_strings_raise(value):
    with pytest.raises(ValueError, match=r"MAJOR\.MINOR"):
        DoclangVersion.parse(value)
    document = DoclangDocument(f'<doclang version="{value}"/>')
    with pytest.raises(ValueError, match=r"MAJOR\.MINOR"):
        document.version()


def test_typed_node_construction_keeps_string_api():
    typed = DoclangNode.element(ElementTag.text)
    typed.set_attribute(AttributeName.class_, "example")
    assert typed.name() == "text"
    assert 'class="example"' in typed.to_xml()
    assert DoclangNode.element("text").name() == "text"
