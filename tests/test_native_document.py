"""Focused tests for the optional native DocLang document API."""

import pytest

from doclang import DoclangDocument


def test_parse_and_lookup():
    xml = (
        '<doclang version="0.7">'
        "<text>Body text</text>"
        "<table><fcel/>cell-a<lcel/><nl/><ched/>head</table>"
        "<picture><caption>Figure caption</caption>"
        '<src uri="assets/image.png"/><text>Picture text</text></picture>'
        "</doclang>"
    )
    doc = DoclangDocument(xml)

    assert doc.valid()
    assert doc.xml() == xml
    assert doc.at(xpath="/doclang[1]/text[1]") == "Body text"
    assert "<text>Body text</text>" in doc.at(xpath="/doclang[1]/text[1]", mode="doclang")
    assert doc.at(xpath="/doclang[1]/table[1]/text()[1]") == "cell-a"
    assert doc.at(xpath="/doclang[1]/table[1]", mode="text") == "cell-a\nhead"
    assert doc.at(xpath="/doclang[1]/picture[1]", mode="text") == "Figure caption\nPicture text"
    assert doc.at(xpath="/doclang[1]/missing[1]") == ""
    assert "not found" in doc.last_error()
    with pytest.raises(TypeError):
        doc.at("/doclang[1]/text[1]")


def test_parse_errors_and_recovery():
    doc = DoclangDocument()
    assert not doc.valid()
    assert not doc.read_xml("<text>missing root</text>")
    assert "root <doclang>" in doc.last_error()
    assert not doc.read_xml("<doclang><text>")
    assert "could not parse" in doc.last_error()
    assert doc.read_xml("<doclang><text>Recovered</text></doclang>")
    assert doc.valid()
    assert doc.last_error() == ""


def test_bounding_boxes_pages_and_iteration():
    doc = DoclangDocument(
        '<doclang version="0.7">'
        '<text><location value="10"/><location value="20.5"/>'
        '<location value="30"/><location value="40"/>First</text>'
        "<page_break/>"
        '<table><cell><location value="0"/><location value="100"/>'
        '<location value="500"/><location value="1000"/>Second</cell></table>'
        "<text>Unlocated</text>"
        "</doclang>"
    )
    first = "/doclang[1]/text[1]"
    second = "/doclang[1]/table[1]/cell[1]"

    assert doc.bounding_box(first) == ((10.0, 20.5), (30.0, 40.0))
    assert doc.page_number(first) == 1
    assert doc.bounding_box(second) == ((0.0, 100.0), (500.0, 1000.0))
    assert doc.page_number(second) == 2
    assert doc.bounding_box("/doclang[1]/text[2]") is None
    assert doc.page_number("/doclang[1]/missing[1]") is None
    assert "not found" in doc.last_error()

    iterator = iter(doc)
    assert iter(iterator) is iterator
    assert [item["name"] for item in iterator] == ["text", "page_break", "table", "text"]
    items = list(doc.iterate_items())
    assert [xpath for xpath, _, _, _ in items] == [
        first,
        "/doclang[1]/page_break[1]",
        "/doclang[1]/table[1]",
        "/doclang[1]/text[2]",
    ]
    assert items[0][2:] == (1, [10, 21, 30, 40])
    assert items[1][2:] == (None, None)
    assert items[2][2:] == (2, None)
    assert next(doc.iterate_items(xpath="/doclang[1]/table[1]"))[0] == second
    assert list(doc.iterate_items_on_page(1)) == items[:1]
    assert list(doc.iterate_items_on_page(2)) == items[2:]
    with pytest.raises(ValueError, match="not found"):
        doc.iterate_items(xpath="/doclang[1]/missing[1]")
    with pytest.raises(ValueError, match="at least 1"):
        doc.iterate_items_on_page(0)


def test_list_expansion_and_iterator_ownership():
    doc = DoclangDocument(
        '<doclang version="0.7">'
        "<list><ldiv><marker>•</marker></ldiv>"
        '<location value="10"/><location value="20"/>'
        '<location value="30"/><location value="40"/>First &amp; more'
        "<ldiv><marker>•</marker></ldiv>Second</list>"
        "<page_break/>"
        "<list><ldiv><marker>a.</marker>Nested one</ldiv>"
        "<ldiv><marker>b.</marker>Nested two</ldiv></list>"
        "</doclang>"
    )
    items = doc.iterate_items()
    del doc

    expanded = list(items)
    assert [xpath for xpath, _, _, _ in expanded] == [
        "/doclang[1]/list[1]/ldiv[1]",
        "/doclang[1]/list[1]/ldiv[2]",
        "/doclang[1]/page_break[1]",
        "/doclang[1]/list[2]/ldiv[1]",
        "/doclang[1]/list[2]/ldiv[2]",
    ]
    assert [item["text"] for _, item, _, _ in expanded if item["name"] == "list_item"] == [
        "First & more",
        "Second",
        "Nested one",
        "Nested two",
    ]
    assert expanded[0][3] == [10, 20, 30, 40]
    assert expanded[2][2:] == (None, None)
