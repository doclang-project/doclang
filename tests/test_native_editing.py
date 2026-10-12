"""Authoring and editing behavior of the native DocLang API."""

from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from doclang import (
    DoclangDocument,
    DoclangFieldItemNode,
    DoclangListNode,
    DoclangNode,
    DoclangPictureNode,
    DoclangTableNode,
    DoclangTextNode,
    DocLangXDocument,
    InsertionSite,
)


def test_explicit_child_and_sibling_edits_are_live():
    doc = DoclangDocument.empty()
    first = DoclangTextNode("First & second")
    assert doc.append_child("/doclang[1]", first) == "/doclang[1]/text[1]"
    assert doc.insert_after("/doclang[1]/text[1]", DoclangTextNode("Third")) == ("/doclang[1]/text[2]")
    doc.prepend_child("/doclang[1]", DoclangTextNode("Zero"))
    assert [row["text"] for row in doc] == ["Zero", "First & second", "Third"]
    doc.delete("/doclang[1]/text[2]")
    assert [row["text"] for row in doc] == ["Zero", "Third"]
    assert "First &amp; second" not in doc.xml()
    assert doc.is_valid() == (True, "")
    assert "First &amp; second" in first.to_xml()


def test_empty_parent_and_failed_edits():
    parent = DoclangNode.element("group")
    parent.append_child(DoclangTextNode("A"))
    parent.prepend_child(DoclangTextNode("B"))
    assert parent.to_xml().index("B") < parent.to_xml().index("A")
    doc = DoclangDocument.empty()
    before = doc.xml()
    with pytest.raises((ValueError, IndexError)):
        doc.insert_before("/doclang[1]", parent)
    with pytest.raises((ValueError, IndexError)):
        doc.delete("/doclang[1]")
    assert doc.xml() == before
    assert not hasattr(DoclangNode.element("text"), "is_valid")


def test_detached_nodes_are_copied_and_iterators_reject_edits():
    node = DoclangTextNode("original")
    first = DoclangDocument.empty()
    second = DoclangDocument.empty()
    first.append_child("/doclang[1]", node)
    second.append_child("/doclang[1]", node)
    node.append_text(" detached")
    assert first.at(xpath="/doclang[1]/text[1]") == "original"
    assert second.at(xpath="/doclang[1]/text[1]") == "original"
    iterator = iter(first)
    first.append_child("/doclang[1]", DoclangTextNode("next"))
    with pytest.raises(RuntimeError, match="changed during iteration"):
        next(iterator)


def test_list_item_ranges_and_table_grid():
    items = DoclangListNode()
    items.append_item_text("tail")
    items.insert_item(0, DoclangTextNode("head"))
    items.append_to_item(0, DoclangPictureNode("image.png"))
    assert items.item_count() == 2
    assert items.is_valid() == (True, "")
    items.delete_item(0)
    assert items.item_count() == 1
    assert "head" not in items.to_xml()
    assert items.is_valid() == (True, "")

    table = DoclangTableNode(2, 2)
    for text in ("first", "second", "third"):
        table.append_to_cell(0, 0, DoclangTextNode(text))
    table.set_cell(0, 1, DoclangPictureNode("plot.png"))
    table.set_caption("Results")
    assert table.is_valid() == (True, "")
    table.insert_row(1)
    table.insert_column(1)
    assert (table.row_count(), table.column_count()) == (3, 3)
    assert table.is_valid() == (True, "")
    table.delete_row(1)
    table.delete_column(1)
    assert (table.row_count(), table.column_count()) == (2, 2)
    assert table.to_xml().count("<text>") == 3
    assert "<picture>" in table.to_xml()
    assert table.is_valid() == (True, "")
    before = table.to_xml()
    with pytest.raises(IndexError):
        table.insert_column(3)
    assert table.to_xml() == before


def test_picture_tabular_and_validation_scopes():
    table = DoclangTableNode(1, 2)
    table.set_cell(0, 0, DoclangTextNode("value"))
    caption = DoclangNode.element("caption")
    caption.append_text("Cell caption")
    table.append_to_cell(0, 1, caption)
    picture = DoclangPictureNode()
    picture.append_child(DoclangNode.element("label"))
    picture.set_caption("Chart")
    picture.set_src("chart.png")
    picture.set_tabular(table)
    assert picture.is_valid() == (True, "")
    assert "Cell caption" in picture.to_xml()
    assert picture.to_xml().index("<label") < picture.to_xml().index("<src")
    assert picture.to_xml().index("<src") < picture.to_xml().index("<tabular")

    doc = DoclangDocument.empty()
    item = DoclangFieldItemNode()
    assert item.validate_local().scope == "local"
    assert item.is_valid() == (True, "")
    site = InsertionSite.append_child("/doclang[1]")
    assert item.validate_in(doc, site).scope == "contextual"
    assert item.is_valid_in(doc, site)[0] is False
    assert picture.is_valid_in(doc, site) == (True, "")
    assert doc.is_valid() == (True, "")
    doc.append_child("/doclang[1]", picture)
    assert doc.is_valid() == (True, "")


def test_local_xsd_errors_and_contextual_checks_do_not_mutate_inputs():
    node = DoclangTextNode("x")
    node.set_attribute("unsupported", "yes")
    report = node.validate_local()
    assert report.scope == "local"
    assert report.xsd_errors
    assert node.is_valid()[0] is False
    doc = DoclangDocument.empty()
    before = doc.xml()
    node_before = node.to_xml()
    assert node.is_valid_in(doc, InsertionSite.append_child("/doclang[1]"))[0] is False
    assert doc.xml() == before
    assert node.to_xml() == node_before


def test_dclx_write_uses_edited_xml(tmp_path):
    path = tmp_path / "edited.dclx"
    doc = DocLangXDocument()
    assert doc.read_xml(DoclangDocument.empty().xml())
    doc.append_child("/doclang[1]", DoclangTextNode("New text"))
    assert doc.write(str(path))
    with ZipFile(path) as archive:
        assert b"New text" in archive.read("document.xml")


def test_dclx_annotation_paths_require_explicit_review_after_edit(tmp_path):
    source = tmp_path / "source.dclx"
    output = tmp_path / "output.dclx"
    with ZipFile(source, "w", ZIP_DEFLATED) as archive:
        archive.writestr("document.xml", DoclangDocument.empty().xml())
        archive.writestr(
            "annotations/properties.csv",
            "type,xpath,label,confidence\nname,/doclang[1]/text[1],example,1\n",
        )
    doc = DocLangXDocument()
    assert doc.read(str(source))
    doc.append_child("/doclang[1]", DoclangTextNode("New text"))
    assert doc.annotations_stale()
    assert not doc.write(str(output))
    assert "annotation XPath" in doc.last_error()
    assert doc.write(str(output), allow_stale_annotations=True)
    assert not doc.annotations_stale()
    with ZipFile(output) as archive:
        assert b"New text" in archive.read("document.xml")
