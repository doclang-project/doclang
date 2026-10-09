"""DCLX coverage for the simplified native annotation records."""

import csv
import io
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pytest

from doclang import ArchiveLimits, DoclangDocument, DoclangTextNode, DocLangXDocument, DoclangXDocument, pack


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


def test_byte_round_trip_custom_parts_and_opc():
    doc = DocLangXDocument()
    assert doc.read_xml('<doclang version="0.7"><heading>Title</heading><text>Body</text></doclang>')
    doc.set_part_bytes("context/provenance.json", b'{"source":"test"}', "application/json")
    doc.set_part_text("assets/note.txt", "caf\u00e9", "text/plain")
    assert doc.set_document_summary("<doclang><text>Summary</text></doclang>")
    assert doc.set_toc(
        '<doclang><toc><entry xpath="/doclang[1]/heading[1]"><description>Title</description></entry></toc></doclang>'
    )
    data = doc.write_bytes()
    with ZipFile(io.BytesIO(data)) as archive:
        assert archive.read("context/provenance.json") == b'{"source":"test"}'
        assert b"application/json" in archive.read("[Content_Types].xml")
        assert b"document.xml" in archive.read("_rels/.rels")

    restored = DocLangXDocument()
    assert restored.read_bytes(data)
    assert restored.get_part_text("assets/note.txt") == "caf\u00e9"
    assert restored.get_part_bytes("context/provenance.json") == b'{"source":"test"}'
    assert restored.validate_package()["ok"]
    restored.remove_part("assets/note.txt")
    assert restored.get_part_text("assets/note.txt") is None
    with pytest.raises(ValueError, match="reserved"):
        restored.set_part_text("document.xml", "bad", "application/xml")


def test_archive_rejects_bad_paths_duplicates_and_limits():
    def package(*parts):
        buffer = io.BytesIO()
        with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
            archive.writestr("document.xml", "<doclang><text>Body</text></doclang>")
            for path, value in parts:
                archive.writestr(path, value)
        return buffer.getvalue()

    for path in ("../outside", "/absolute", "a/../b", "a\\b"):
        doc = DocLangXDocument()
        assert not doc.read_bytes(package((path, b"x")))
    doc = DocLangXDocument()
    assert not doc.read_bytes(package(("document.xml", b"duplicate")))
    assert "duplicate" in doc.last_error()
    bounds = ArchiveLimits()
    bounds.max_entry_bytes = 10
    assert not DocLangXDocument().read_bytes(package(("assets/large", b"01234567890")), bounds)
    ratio_bounds = ArchiveLimits()
    ratio_bounds.max_compression_ratio = 2
    assert not DocLangXDocument().read_bytes(package(("assets/repetitive", b"x" * 1000)), ratio_bounds)


def test_sidecar_staleness_and_structured_nodes():
    doc = DocLangXDocument()
    assert doc.read_xml('<doclang version="0.7"><heading>Title</heading><text>Body</text></doclang>')
    assert not doc.set_toc(
        '<doclang><toc><entry xpath="/doclang[1]/missing[1]"><description>Bad</description></entry></toc></doclang>'
    )
    assert doc.set_toc(
        '<doclang><toc><entry xpath="/doclang[1]/heading[1]"><description>Title</description></entry></toc></doclang>'
    )
    nodes = doc.iter_nodes("/doclang[1]", limit=3)
    assert [item["name"] for item in nodes] == ["doclang", "heading", "text"]
    assert nodes[1]["xpath"] == "/doclang[1]/heading[1]"
    assert nodes[1]["page"] == 1
    assert len(doc.iter_nodes(limit=2)) == 2
    doc.append_child("/doclang[1]", DoclangTextNode("Extra"))
    assert doc.sidecars_stale()
    with pytest.raises(ValueError, match="sidecars"):
        doc.write_bytes()
    assert doc.set_toc(
        '<doclang><toc><entry xpath="/doclang[1]/heading[1]"><description>Title</description></entry></toc></doclang>'
    )
    assert not doc.sidecars_stale()
    assert doc.write_bytes()


def test_package_validation_reports_bad_metadata_and_source_refs():
    buffer = io.BytesIO()
    with ZipFile(buffer, "w", ZIP_DEFLATED) as archive:
        archive.writestr(
            "document.xml",
            '<doclang version="0.7"><picture><src uri="assets/missing.png"/></picture></doclang>',
        )
        archive.writestr("[Content_Types].xml", "<Types></Types>")
        archive.writestr("_rels/.rels", "<Relationships></Relationships>")
    doc = DocLangXDocument()
    assert doc.read_bytes(buffer.getvalue())
    codes = {item["code"] for item in doc.validate_package()["errors"]}
    assert {
        "invalid_document_type",
        "invalid_relationship_type",
        "document_relation_count",
        "missing_source_part",
    } <= codes
    doc.set_part_bytes("assets/missing.png", b"image", "image/png")
    restored = DocLangXDocument()
    assert restored.read_bytes(doc.write_bytes())
    assert restored.validate_package()["ok"]


def test_package_validation_checks_page_alignment():
    doc = DocLangXDocument()
    assert doc.read_xml('<doclang version="0.7"><text>One page</text></doclang>')
    doc.set_part_bytes("pages/2.png", b"image", "image/png")
    restored = DocLangXDocument()
    assert restored.read_bytes(doc.write_bytes())
    assert "invalid_media_index" in {issue["code"] for issue in restored.validate_package()["errors"]}


def test_native_round_trip_of_python_packed_media(tmp_path):
    demo = Path(__file__).resolve().parents[1] / "examples" / "archive-demo"
    source = pack(demo / "document.xml", output=tmp_path / "source.dclx", pages=demo / "pages", audio=demo / "audio")
    doc = DocLangXDocument()
    assert doc.read(str(source))
    assert doc.validate_package()["ok"]
    restored = DocLangXDocument()
    assert restored.read_bytes(doc.write_bytes())
    assert restored.validate_package()["ok"]
    assert restored.get_part_bytes("pages/1.png") == (demo / "pages" / "1.png").read_bytes()
    assert restored.get_part_bytes("audio/1.wav") == (demo / "audio" / "1.wav").read_bytes()
