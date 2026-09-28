"""DCLX coverage for the simplified native annotation records."""

import csv
import io
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from doclang import DoclangDocument, DocLangXDocument, DoclangXDocument


def _csv(*rows):
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(rows)
    return output.getvalue()


def _create_dclx(path):
    ehash = DocLangXDocument.hash("FeSe")
    with ZipFile(path, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "document.xml",
            '<doclang version="0.7"><text>FeSe is a material.</text>'
            "<table><fcel/>A<lcel/>B<nl/><fcel/>C</table></doclang>",
        )
        archive.writestr(
            "annotations/properties.csv",
            _csv(
                ("type", "xpath", "label", "confidence"),
                ("language", "/doclang[1]/text[1]", "en", "0.99"),
            ),
        )
        archive.writestr(
            "annotations/instances.csv",
            _csv(
                ("type", "subtype", "xpath", "conf", "ehash", "ihash", "char_i", "char_j", "name", "original"),
                ("term", "", "/doclang[1]/text[1]", "1", str(ehash), "123", "0", "4", "FeSe", "FeSe"),
            ),
        )
        archive.writestr(
            "annotations/relations.csv",
            _csv(("name", "conf", "hash_i", "hash_j"), ("contains", "0.8", str(ehash), "42")),
        )
        archive.writestr("annotations/edges.csv", "legacy graph edges")
        archive.writestr("assets/keep.bin", b"opaque payload")


def test_dclx_tables_queries_and_round_trip(tmp_path):
    pd = pytest.importorskip("pandas")
    assert DoclangXDocument is DocLangXDocument
    source = tmp_path / "source.dclx"
    output = tmp_path / "output.dclx"
    _create_dclx(source)

    doc = DocLangXDocument()
    assert isinstance(doc, DoclangDocument)
    assert doc.read(str(source))
    assert doc.valid() and doc.has_archive() and doc.has_annotations()
    assert doc.source_path() == str(source)
    assert "assets/keep.bin" in doc.archive_paths()
    assert "annotations/edges.csv" not in doc.annotation_paths()
    assert doc.overview()["entities"] == 1  # derived from instances.csv
    assert "edges" not in doc.overview()

    properties = doc.properties()
    instances = doc.instances()
    entities = doc.entities()
    relations = doc.relations()
    assert isinstance(properties, pd.DataFrame)
    assert properties.columns.tolist() == ["type", "xpath", "label", "confidence"]
    assert instances.columns.tolist() == [
        "type",
        "subtype",
        "xpath",
        "conf",
        "ehash",
        "ihash",
        "char_i",
        "char_j",
        "name",
        "original",
    ]
    assert entities.columns.tolist() == ["type", "subtype", "name", "ehash", "count"]
    assert relations.columns.tolist() == ["name", "conf", "hash_i", "hash_j"]
    assert str(properties.dtypes["type"]) == "string"
    assert str(properties.dtypes["confidence"]) == "Float32"
    assert str(instances.dtypes["ehash"]) == "UInt64"
    assert str(relations.dtypes["conf"]) == "Float32"
    assert entities.loc[0, "ehash"] == DocLangXDocument.hash("FeSe")
    assert entities.loc[0, "count"] == 1
    assert instances.loc[0, "xpath"] == "/doclang[1]/text[1]"
    assert len(doc.query_properties(type="language", xpath="/doclang[1]/text[1]")) == 1
    assert len(doc.query_entities(name_contains="Fe", min_count=1)) == 1
    assert len(doc.query_instances(entity_hash=DocLangXDocument.hash("FeSe"))) == 1
    assert len(doc.query_instances(name="missing")) == 0
    assert len(doc.query_relations(name_contains="contain", hash_j=42)) == 1
    assert len(doc.query_relations(min_conf=0.9)) == 0

    assert doc.table_coordinates("/doclang[1]/table[1]/text()[1]") == (0, 0)
    assert doc.table_coordinates("/doclang[1]/table[1]/text()[2]") == (0, 1)
    assert doc.table_coordinates("/doclang[1]/table[1]/text()[3]") == (1, 0)
    assert doc.table_coordinates("/doclang[1]/text[1]") is None
    assert doc.table_coordinates("/doclang[1]/missing[1]") is None
    assert "not found" in doc.last_error()

    assert doc.write(str(output))
    with ZipFile(output) as archive:
        assert archive.read("assets/keep.bin") == b"opaque payload"
        assert "annotations/edges.csv" not in archive.namelist()
        assert archive.read("annotations/entities.csv").startswith(b"type,subtype,name,ehash,count")
        assert archive.read("annotations/instances.csv").startswith(b"type,subtype,xpath,conf,ehash")

    restored = DocLangXDocument()
    assert restored.read(str(output))
    assert restored.at(xpath="/doclang[1]/text[1]") == "FeSe is a material."
    assert restored.overview()["entities"] == 1
    assert len(restored.query_instances(name="FeSe")) == 1


def test_sidecars_clear_and_plain_xml_replaces_dclx_state(tmp_path):
    output = tmp_path / "sidecars.dclx"
    doc = DocLangXDocument()
    assert doc.read_xml('<doclang version="0.7"><text>Body</text></doclang>')
    doc.set_document_reference("@article{document}\n")
    doc.set_references("@article{reference}\n")
    assert doc.set_document_summary("<doclang><text>Summary</text></doclang>")
    assert doc.set_toc(
        '<doclang><toc><entry xpath="/doclang[1]/text[1]"><description>Body</description></entry></toc></doclang>'
    )
    assert doc.set_concepts("<doclang><concepts><concept><header>FeSe</header></concept></concepts></doclang>")
    assert doc.write(str(output))

    restored = DocLangXDocument()
    assert restored.read(str(output))
    assert restored.document_reference() == "@article{document}\n"
    assert restored.references() == "@article{reference}\n"
    assert isinstance(restored.summary(), DoclangDocument)
    assert restored.summary().at(xpath="/doclang[1]/text[1]") == "Summary"
    assert "<toc>" in restored.toc().xml()
    assert "<header>FeSe</header>" in restored.concepts().xml()

    assert not restored.set_toc("<doclang><toc><entry /></toc></doclang>")
    assert "entries require xpath" in restored.last_error()
    assert restored.toc() is not None
    restored.clear_document_reference()
    restored.clear_references()
    restored.clear_document_summary()
    restored.clear_toc()
    restored.clear_concepts()
    assert all(
        value is None
        for value in (
            restored.document_reference(),
            restored.references(),
            restored.summary(),
            restored.toc(),
            restored.concepts(),
        )
    )

    assert restored.read_xml("<doclang><text>Replacement</text></doclang>")
    assert restored.valid() and not restored.has_archive() and not restored.has_annotations()
    assert restored.source_path() == ""
    assert restored.overview()["instances"] == 0


def test_old_annotation_columns_are_rejected(tmp_path):
    source = tmp_path / "old-schema.dclx"
    with ZipFile(source, "w") as archive:
        archive.writestr("document.xml", "<doclang><text>Body</text></doclang>")
        archive.writestr("annotations/properties.csv", "type,subj_path,label,confidence\n")

    doc = DocLangXDocument()
    assert not doc.read(str(source))
    assert "unexpected header in annotations/properties.csv" in doc.last_error()
