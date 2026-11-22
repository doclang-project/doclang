"""Original source storage belongs exclusively to DCLX packages."""

import io
from xml.etree import ElementTree
from zipfile import ZipFile

import pytest

from doclang import ArchiveLimits, DoclangDocument, DoclangTextNode, DocLangXDocument

XML = '<doclang xmlns="https://www.doclang.ai/ns/v0"><text>Body</text></doclang>'
PAYLOAD = b"%PDF-1.7\n\x00\xff\x80original\r\n"


@pytest.mark.parametrize("as_document", [False, True])
@pytest.mark.parametrize("payload", [None, PAYLOAD, b""])
def test_constructor_with_xml_or_document(as_document, payload):
    argument = DoclangDocument(XML) if as_document else XML
    kwargs = {} if payload is None else {"source": payload, "source_mimetype": "application/pdf"}
    doc = DocLangXDocument(argument, **kwargs)
    assert doc.valid()
    assert doc.xml() == XML
    assert doc.get_source() == (None if payload is None else (payload, "application/pdf"))
    restored = DocLangXDocument()
    assert restored.read_bytes(doc.write_bytes())
    assert restored.valid()
    assert restored.at(xpath="/doclang[1]/text[1]") == "Body"
    assert restored.validate_package()["ok"]
    assert restored.get_source() == doc.get_source()


def test_document_constructor_copies_current_xml_independently():
    original = DoclangDocument(XML)
    original.append_child("/doclang[1]", DoclangTextNode("Before copy"))
    package = DocLangXDocument(dclg=original, source=PAYLOAD, source_mimetype="application/pdf")
    copied_xml = package.xml()
    assert "Before copy" in copied_xml
    original.append_child("/doclang[1]", DoclangTextNode("Original only"))
    assert package.xml() == copied_xml
    package.append_child("/doclang[1]", DoclangTextNode("Package only"))
    assert "Package only" not in original.xml()
    assert "Original only" not in package.xml()
    assert package.get_source() == (PAYLOAD, "application/pdf")


def test_xml_keyword_constructor_and_invalid_xml():
    assert DocLangXDocument(xml=XML).xml() == XML
    doc = DocLangXDocument("<doclang><text>", source=PAYLOAD, source_mimetype="application/pdf")
    assert not doc.valid()
    assert "could not parse" in doc.last_error()
    assert doc.get_source() == (PAYLOAD, "application/pdf")
    assert not DocLangXDocument(DoclangDocument()).valid()
    with pytest.raises(TypeError):
        DocLangXDocument(XML, PAYLOAD, "application/pdf")


def _archive(parts):
    buffer = io.BytesIO()
    with ZipFile(buffer, "w") as archive:
        archive.writestr("document.xml", XML)
        for path, value in parts.items():
            archive.writestr(path, value)
    return buffer.getvalue()


def _overrides(data):
    with ZipFile(io.BytesIO(data)) as archive:
        types = ElementTree.fromstring(archive.read("[Content_Types].xml"))
    return {entry.attrib["PartName"]: entry.attrib["ContentType"] for entry in types if entry.tag.endswith("}Override")}


@pytest.mark.parametrize("payload", [PAYLOAD, b""])
def test_source_round_trip_and_clear(tmp_path, payload):
    doc = DocLangXDocument(source=payload, source_mimetype="application/pdf")
    assert doc.read_xml(XML)
    assert doc.has_source()
    assert doc.get_source() == (payload, "application/pdf")
    assert doc.get_part_bytes("source/document") == payload
    assert doc.get_part_text("source/mimetype") == "application/pdf"

    data = doc.write_bytes()
    overrides = _overrides(data)
    assert overrides["/source/document"] == "application/pdf"
    assert overrides["/source/mimetype"] == "text/plain"
    restored = DocLangXDocument()
    assert restored.read_bytes(data)
    assert restored.get_source() == (payload, "application/pdf")
    assert restored.validate_package()["ok"]
    assert restored.write(str(tmp_path / "source.dclx"))
    assert restored.read(str(tmp_path / "source.dclx"))
    assert restored.get_source() == (payload, "application/pdf")

    restored.set_source(b"replacement", "text/plain")
    assert restored.get_source() == (b"replacement", "text/plain")
    assert _overrides(restored.write_bytes())["/source/document"] == "text/plain"
    restored.clear_source()
    restored.clear_source()
    assert not restored.has_source()
    assert restored.get_source() is None
    cleared = restored.write_bytes()
    with ZipFile(io.BytesIO(cleared)) as archive:
        assert "source/document" not in archive.namelist()
        assert "source/mimetype" not in archive.namelist()
    assert "/source/document" not in _overrides(cleared)
    assert "/source/mimetype" not in _overrides(cleared)


def test_source_lifecycle_and_xml_only_boundary(tmp_path):
    assert not hasattr(DoclangDocument(), "set_source")
    doc = DocLangXDocument()
    assert doc.get_source() is None
    assert not doc.has_source()
    doc.set_source(PAYLOAD, "application/pdf")
    assert doc.read_xml(XML)
    doc.append_child("/doclang[1]", DoclangTextNode("Added"))
    assert doc.get_source() == (PAYLOAD, "application/pdf")
    assert doc.read_xml(XML)
    assert doc.get_source() == (PAYLOAD, "application/pdf")
    assert not doc.read_xml("invalid XML")
    assert doc.get_source() == (PAYLOAD, "application/pdf")
    assert doc.last_error()
    assert doc.read_bytes(_archive({}))
    assert doc.get_source() is None
    doc.set_source(PAYLOAD, "application/pdf")
    path = tmp_path / "other.dclg"
    path.write_text(XML)
    assert doc.read(str(path))
    assert doc.get_source() is None
    doc.set_source(PAYLOAD, "application/pdf")
    assert not doc.read_bytes(b"invalid archive")
    assert doc.get_source() is None


@pytest.mark.parametrize("kwargs", [{"source": b""}, {"source_mimetype": "application/pdf"}])
@pytest.mark.parametrize("args", [(), (XML,), (DoclangDocument(XML),)])
def test_constructor_requires_source_pair(kwargs, args):
    with pytest.raises(ValueError, match="together"):
        DocLangXDocument(*args, **kwargs)


@pytest.mark.parametrize(
    "mimetype",
    [
        "",
        "pdf",
        "/pdf",
        "application/",
        "application/pdf/extra",
        "application/pdf\n",
        "application/pdf\x00",
        " application/pdf",
        "application/pdƒ",
        "*/*",
    ],
)
def test_invalid_source_update_is_atomic(mimetype):
    doc = DocLangXDocument(source=PAYLOAD, source_mimetype="application/pdf")
    with pytest.raises(ValueError, match="MIME"):
        doc.set_source(b"replacement", mimetype)
    assert doc.get_source() == (PAYLOAD, "application/pdf")


@pytest.mark.parametrize(
    "parts",
    [
        {"source/mimetype": b"application/pdf"},
        {"source/document": PAYLOAD},
        {"source/mimetype": b"invalid", "source/document": PAYLOAD},
        {"source/mimetype": b"application/pdf\n\n", "source/document": PAYLOAD},
    ],
)
def test_reader_rejects_malformed_source(parts):
    doc = DocLangXDocument()
    assert not doc.read_bytes(_archive(parts))
    assert "source/" in doc.last_error()


def test_source_line_ending_metadata_validation_and_archive_limits():
    data = _archive({"source/mimetype": b"application/pdf\r\n", "source/document": PAYLOAD})
    doc = DocLangXDocument()
    assert doc.read_bytes(data)
    assert doc.get_source() == (PAYLOAD, "application/pdf")
    assert any(error["code"] == "invalid_source_type" for error in doc.validate_package()["errors"])
    repaired = doc.write_bytes()
    assert doc.read_bytes(repaired)
    assert doc.validate_package()["ok"]
    limits = ArchiveLimits()
    limits.max_entry_bytes = 10
    assert not doc.read_bytes(data, limits)


@pytest.mark.parametrize("path", ["source/document", "source/mimetype"])
def test_source_parts_require_dedicated_setter(path):
    doc = DocLangXDocument()
    with pytest.raises(ValueError, match="reserved"):
        doc.set_part_bytes(path, b"data", "text/plain")
    with pytest.raises(ValueError, match="reserved"):
        doc.remove_part(path)
