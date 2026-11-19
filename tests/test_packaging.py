"""Tests for DocLang archive packaging."""

from __future__ import annotations

import zipfile
from pathlib import Path
from xml.etree import ElementTree

import pytest

from doclang import PackagingError, ValidationError, pack
from doclang._packaging import _check_archive

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DEMO = REPO_ROOT / "examples" / "archive-demo"
VALID_DIR = Path(__file__).parent / "data" / "valid"


def _zip_members(archive_path: Path) -> set[str]:
    with zipfile.ZipFile(archive_path) as archive:
        return set(archive.namelist())


def test_pack_markup_only_default_output(tmp_path: Path) -> None:
    document = tmp_path / "markup.dclg"
    document.write_text((ARCHIVE_DEMO / "document.xml").read_text(encoding="utf-8"), encoding="utf-8")

    created = pack(document)

    assert created == document.with_suffix(".dclx").resolve()
    members = _zip_members(created)
    assert "document.xml" in members
    assert "[Content_Types].xml" in members
    assert "_rels/.rels" in members
    assert not any(member.startswith("pages/") for member in members)


def test_pack_markup_only_explicit_output(tmp_path: Path) -> None:
    document = ARCHIVE_DEMO / "document.xml"
    output = tmp_path / "report.dclx"

    created = pack(document, output=output)

    assert created == output.resolve()
    members = _zip_members(created)
    assert "document.xml" in members


SOURCE_RELATIONSHIP = "http://doclang.ai/ns/package/2026/relationships/source"
SOURCE_METADATA_RELATIONSHIP = "http://doclang.ai/ns/package/2026/relationships/source-metadata"


def _content_types(archive_path: Path) -> tuple[dict[str, str], dict[str, str]]:
    """The ``<Default>`` content types by extension and the ``<Override>`` ones by part name."""
    with zipfile.ZipFile(archive_path) as archive:
        content_types = ElementTree.fromstring(archive.read("[Content_Types].xml"))
    defaults = {e.attrib["Extension"]: e.attrib["ContentType"] for e in content_types if e.tag.endswith("Default")}
    overrides = {e.attrib["PartName"]: e.attrib["ContentType"] for e in content_types if e.tag.endswith("Override")}
    return defaults, overrides


def _relationships(archive_path: Path) -> dict[str, str]:
    """The targets of the package relationships by type."""
    with zipfile.ZipFile(archive_path) as archive:
        rels = ElementTree.fromstring(archive.read("_rels/.rels"))
    return {e.attrib["Type"]: e.attrib["Target"] for e in rels}


@pytest.mark.parametrize("from_path", [False, True])
@pytest.mark.parametrize("original", [b"%PDF-1.7\n\x00\xff\n", b""])
def test_pack_source_is_stored_with_the_extension_of_its_name(tmp_path: Path, from_path: bool, original: bytes) -> None:
    source_path = tmp_path / "original.pdf"
    source_path.write_bytes(original)
    output = tmp_path / "with-source.dclx"

    pack(
        ARCHIVE_DEMO / "document.xml",
        output=output,
        source=source_path if from_path else original,
        source_name=None if from_path else "original.pdf",
        source_mimetype="application/pdf",
    )

    with zipfile.ZipFile(output) as archive:
        assert archive.read("source.pdf") == original
    defaults, overrides = _content_types(output)
    assert defaults["pdf"] == "application/pdf" and "/source.pdf" not in overrides
    assert _relationships(output)[SOURCE_RELATIONSHIP] == "source.pdf"
    assert _check_archive(output, None) == ([], [])


def test_pack_source_with_a_known_extension_needs_no_mimetype(tmp_path: Path) -> None:
    recording = tmp_path / "Episode 12.MP3"
    recording.write_bytes(b"mp3")
    output = tmp_path / "out.dclx"

    pack(ARCHIVE_DEMO / "document.xml", output=output, source=recording)

    assert "source.mp3" in _zip_members(output)
    defaults, overrides = _content_types(output)
    assert defaults["mp3"] == "audio/mpeg" and "/source.mp3" not in overrides
    assert SOURCE_METADATA_RELATIONSHIP not in _relationships(output)  # the original name is opt-in
    assert "source-metadata.xml" not in _zip_members(output)


@pytest.mark.parametrize("name", [None, "notes", "archive.tar~", ".bashrc", "x.rels"])
def test_pack_source_without_a_reliable_extension_gets_an_override(tmp_path: Path, name: str | None) -> None:
    output = tmp_path / "out.dclx"

    pack(ARCHIVE_DEMO / "document.xml", output=output, source=b"data", source_name=name, source_mimetype="text/plain")

    assert "source" in _zip_members(output)
    assert _content_types(output)[1]["/source"] == "text/plain"
    assert _relationships(output)[SOURCE_RELATIONSHIP] == "source"
    assert _check_archive(output, None) == ([], [])


def test_pack_source_mimetype_differing_from_the_default_gets_an_override(tmp_path: Path) -> None:
    output = tmp_path / "out.dclx"

    pack(ARCHIVE_DEMO / "document.xml", output=output, source=b"v", source_name="clip.ogg", source_mimetype="video/ogg")

    defaults, overrides = _content_types(output)
    assert overrides["/source.ogg"] == "video/ogg" and "ogg" not in defaults  # no part left for the default


def test_pack_declares_only_the_extensions_present(tmp_path: Path) -> None:
    output = tmp_path / "out.dclx"

    pack(
        ARCHIVE_DEMO / "document.xml", output=output, audio=ARCHIVE_DEMO / "audio", source=b"%PDF", source_name="a.pdf"
    )

    defaults, _ = _content_types(output)
    assert set(defaults) == {"rels", "wav", "pdf"}


def test_pack_source_without_a_content_type_is_refused(tmp_path: Path) -> None:
    output = tmp_path / "out.dclx"
    with pytest.raises(PackagingError, match="No content type known"):
        pack(ARCHIVE_DEMO / "document.xml", output=output, source=b"data")
    with pytest.raises(PackagingError, match="No content type known"):
        pack(ARCHIVE_DEMO / "document.xml", output=output, source=b"data", source_name="report.xyz")
    assert not output.exists()


def test_pack_source_name_is_recorded_in_a_descriptor(tmp_path: Path) -> None:
    original = tmp_path / "upload-3f2a.bin"
    original.write_bytes(b"%PDF")
    output = tmp_path / "out.dclx"

    pack(
        ARCHIVE_DEMO / "document.xml",
        output=output,
        source=original,
        source_name='Q3 "final" & co.pdf',
        source_mimetype="application/pdf",
    )

    relationships = _relationships(output)
    assert relationships[SOURCE_RELATIONSHIP] == "source.pdf"  # the extension of the original name
    assert relationships[SOURCE_METADATA_RELATIONSHIP] == "source-metadata.xml"
    with zipfile.ZipFile(output) as archive:
        descriptor = ElementTree.fromstring(archive.read("source-metadata.xml"))
    assert descriptor.tag == "{http://doclang.ai/ns/package/2026/source-metadata}source"
    assert descriptor.attrib == {"name": 'Q3 "final" & co.pdf'}
    assert _content_types(output)[1]["/source-metadata.xml"] == "application/vnd.doclang.source-metadata+xml"
    assert _check_archive(output, None) == ([], [])


@pytest.mark.parametrize(
    ("name", "part"),
    [
        ("backup.tar.gz", "source.tar.gz"),
        ("Report.Final.PDF", "source.final.pdf"),
        ("a.b.c.gz", "source.c.gz"),  # at most two extensions
        ("x.tar~.gz", "source.gz"),  # only reliable ones
        ("tar.gz", "source.gz"),  # the stem is not an extension
        ("data.xml", "source.xml"),  # no clash with the descriptor
    ],
)
def test_pack_source_keeps_up_to_two_extensions(tmp_path: Path, name: str, part: str) -> None:
    output = tmp_path / "out.dclx"

    pack(ARCHIVE_DEMO / "document.xml", output=output, source=b"x", source_name=name, source_mimetype="text/x-test")

    relationships = _relationships(output)
    assert relationships[SOURCE_RELATIONSHIP] == part
    assert relationships[SOURCE_METADATA_RELATIONSHIP] == "source-metadata.xml"
    defaults, overrides = _content_types(output)
    assert defaults.get(part.rsplit(".", 1)[1]) == "text/x-test" or overrides.get(f"/{part}") == "text/x-test"
    assert _check_archive(output, None) == ([], [])


@pytest.mark.parametrize("as_mapping", [False, True])
def test_pack_reuses_a_source_file_already_packed(tmp_path: Path, as_mapping: bool) -> None:
    output = tmp_path / "out.dclx"
    recording = ARCHIVE_DEMO / "audio" / "1.wav"

    pack(
        ARCHIVE_DEMO / "document.xml",
        output=output,
        audio={1: recording} if as_mapping else ARCHIVE_DEMO / "audio",
        source=recording,
        source_name="episode-12.wav",
    )

    assert _relationships(output)[SOURCE_RELATIONSHIP] == "audio/1.wav"
    assert "source.wav" not in _zip_members(output)  # no second copy
    assert _check_archive(output, None) == ([], [])


def test_pack_rejects_inconsistent_source_options(tmp_path: Path) -> None:
    document = ARCHIVE_DEMO / "document.xml"
    output = tmp_path / "bad.dclx"

    with pytest.raises(PackagingError, match="need source"):
        pack(document, output=output, source_mimetype="application/pdf")
    with pytest.raises(PackagingError, match="need source"):
        pack(document, output=output, source_name="a.pdf")
    for name in ["", "dir/a.pdf", "a\nb.pdf"]:
        with pytest.raises(PackagingError, match="Invalid source file name"):
            pack(document, output=output, source=b"", source_name=name, source_mimetype="application/pdf")
    assert not output.exists()


def test_pack_escapes_source_mimetype(tmp_path: Path) -> None:
    output = tmp_path / "escaped.dclx"
    mimetype = "application/x-a&b"

    pack(ARCHIVE_DEMO / "document.xml", output=output, source=b"data", source_mimetype=mimetype)

    assert _content_types(output)[1]["/source"] == mimetype


def test_pack_rejects_invalid_source_mimetype(tmp_path: Path) -> None:
    output = tmp_path / "invalid-mimetype.dclx"

    with pytest.raises(PackagingError, match="Invalid source MIME type"):
        pack(
            ARCHIVE_DEMO / "document.xml",
            output=output,
            source=b"data",
            source_mimetype='application/pdf" bad="true',
        )
    assert not output.exists()


def test_pack_rejects_symlink_source(tmp_path: Path) -> None:
    original = tmp_path / "original.pdf"
    original.write_bytes(b"pdf")
    source_link = tmp_path / "linked.pdf"
    source_link.symlink_to(original)
    output = tmp_path / "symlink-source.dclx"

    with pytest.raises(PackagingError, match="symbolic link"):
        pack(
            ARCHIVE_DEMO / "document.xml",
            output=output,
            source=source_link,
            source_mimetype="application/pdf",
        )
    assert not output.exists()


def test_pack_with_pages_directory(tmp_path: Path) -> None:
    document = ARCHIVE_DEMO / "document.xml"
    output = tmp_path / "demo.dclx"

    pack(document, output=output, pages=ARCHIVE_DEMO / "pages")

    members = _zip_members(output)
    assert "pages/1.png" in members
    assert "pages/3.png" in members


def test_pack_with_pages_sequence(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_description_element_head.dclg"
    page_one = ARCHIVE_DEMO / "pages" / "1.png"
    page_two = ARCHIVE_DEMO / "pages" / "3.png"
    output = tmp_path / "ordered.dclx"

    pack(document, output=output, pages=[page_one, page_two])

    members = _zip_members(output)
    assert "pages/1.png" in members
    assert "pages/2.png" in members


def test_pack_with_pages_mapping(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_description_element_head.dclg"
    page_one = ARCHIVE_DEMO / "pages" / "1.png"
    page_three = ARCHIVE_DEMO / "pages" / "3.png"
    output = tmp_path / "mapped.dclx"

    pack(document, output=output, pages={1: page_one, 3: page_three})

    members = _zip_members(output)
    assert "pages/1.png" in members
    assert "pages/3.png" in members
    assert "pages/2.png" not in members


def test_pack_archive_demo_with_audio_directory(tmp_path: Path) -> None:
    output = tmp_path / "demo.dclx"

    pack(
        ARCHIVE_DEMO / "document.xml",
        output=output,
        pages=ARCHIVE_DEMO / "pages",
        audio=ARCHIVE_DEMO / "audio",
        validate=True,
    )

    members = _zip_members(output)
    assert "audio/1.wav" in members
    assert "pages/1.png" in members


def test_pack_with_audio_and_video_mapping(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_track_frame_audio.dclg"
    source = ARCHIVE_DEMO / "pages" / "1.png"
    track_two_audio = tmp_path / "two.mp3"
    track_two_audio.write_bytes(source.read_bytes())
    track_three_video = tmp_path / "three.mp4"
    track_three_video.write_bytes(source.read_bytes())
    output = tmp_path / "media.dclx"

    pack(document, output=output, audio={2: track_two_audio}, video={3: track_three_video})

    members = _zip_members(output)
    assert "audio/2.mp3" in members
    assert "video/3.mp4" in members
    assert "audio/1.mp3" not in members


def test_pack_with_audio_sequence_renumbers_from_one(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_track_frame_audio.dclg"
    source = ARCHIVE_DEMO / "pages" / "1.png"
    first = tmp_path / "a.ogg"
    first.write_bytes(source.read_bytes())
    output = tmp_path / "seq.dclx"

    pack(document, output=output, audio=[first])

    assert "audio/1.ogg" in _zip_members(output)


def test_pack_with_video_directory_preserves_names(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_track_frame_audio.dclg"
    source = ARCHIVE_DEMO / "pages" / "1.png"
    video_dir = tmp_path / "clips"
    video_dir.mkdir()
    (video_dir / "3.webm").write_bytes(source.read_bytes())
    output = tmp_path / "viddir.dclx"

    pack(document, output=output, video=video_dir)

    assert "video/3.webm" in _zip_members(output)


def test_pack_rejects_zero_audio_track_number(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_track_frame_audio.dclg"
    source = tmp_path / "a.mp3"
    source.write_bytes(b"audio")

    with pytest.raises(PackagingError, match="positive integers"):
        pack(document, output=tmp_path / "bad.dclx", audio={0: source})


def test_pack_rejects_symlink_audio_file(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_track_frame_audio.dclg"
    secret = tmp_path / "secret.mp3"
    secret.write_bytes(b"audio")
    link = tmp_path / "1.mp3"
    link.symlink_to(secret)
    output = tmp_path / "symlink-audio.dclx"

    with pytest.raises(PackagingError, match="symbolic link"):
        pack(document, output=output, audio=[link])

    assert not output.exists()


def test_pack_with_asset_mapping(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_description_element_head.dclg"
    asset_source = ARCHIVE_DEMO / "pages" / "1.png"
    output = tmp_path / "assets.dclx"

    pack(
        document,
        output=output,
        assets={"chart.svg": asset_source, "img/sample.png": asset_source},
    )

    members = _zip_members(output)
    assert "assets/chart.svg" in members
    assert "assets/img/sample.png" in members


def test_pack_with_assets_directory(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_description_element_head.dclg"
    assets_dir = tmp_path / "payload"
    nested = assets_dir / "img"
    nested.mkdir(parents=True)
    source = ARCHIVE_DEMO / "pages" / "1.png"
    (assets_dir / "chart.svg").write_bytes(source.read_bytes())
    (nested / "sample.png").write_bytes(source.read_bytes())
    output = tmp_path / "assets-dir.dclx"

    pack(document, output=output, assets=assets_dir)

    members = _zip_members(output)
    assert "assets/chart.svg" in members
    assert "assets/img/sample.png" in members


def test_pack_validate_invalid_document(tmp_path: Path) -> None:
    document = Path(__file__).parent / "data" / "invalid" / "nok_summary_in_doclang.dclg"
    output = tmp_path / "invalid.dclx"

    with pytest.raises(ValidationError):
        pack(document, output=output, validate=True)

    assert not output.exists()


def test_pack_validate_checks_the_archive(tmp_path: Path) -> None:
    output = tmp_path / "out.dclx"
    recording = ARCHIVE_DEMO / "audio" / "1.wav"

    with pytest.raises(ValidationError, match=r"audio/2\.wav: Whole-track media for <track> 2"):
        pack(ARCHIVE_DEMO / "document.xml", output=output, audio=[recording, recording], validate=True)

    assert not output.exists()


def test_pack_missing_document(tmp_path: Path) -> None:
    with pytest.raises(PackagingError, match="Document not found"):
        pack(tmp_path / "missing.dclg")


def test_pack_invalid_asset_path(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_description_element_head.dclg"
    asset_source = ARCHIVE_DEMO / "pages" / "1.png"

    with pytest.raises(PackagingError, match="Invalid asset path"):
        pack(
            document,
            output=tmp_path / "bad-asset.dclx",
            assets={"../escape.svg": asset_source},
        )


def test_pack_rejects_symlink_asset_file(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_description_element_head.dclg"
    secret = tmp_path / "secret.txt"
    secret.write_text("sensitive", encoding="utf-8")
    link = tmp_path / "chart.svg"
    link.symlink_to(secret)
    output = tmp_path / "symlink-asset.dclx"

    with pytest.raises(PackagingError, match="symbolic link"):
        pack(document, output=output, assets={"chart.svg": link})

    assert not output.exists()


def test_pack_rejects_symlink_in_assets_directory(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_description_element_head.dclg"
    secret = tmp_path / "secret.txt"
    secret.write_text("sensitive", encoding="utf-8")
    assets_dir = tmp_path / "payload"
    assets_dir.mkdir()
    (assets_dir / "chart.svg").symlink_to(secret)
    output = tmp_path / "symlink-assets-dir.dclx"

    with pytest.raises(PackagingError, match="symbolic link"):
        pack(document, output=output, assets=assets_dir)

    assert not output.exists()


def test_pack_rejects_nested_symlink_directory_in_assets(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_description_element_head.dclg"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "leak.png").write_bytes(b"png")
    assets_dir = tmp_path / "payload"
    assets_dir.mkdir()
    (assets_dir / "img").symlink_to(outside)
    output = tmp_path / "symlink-assets-subdir.dclx"

    with pytest.raises(PackagingError, match="symbolic link"):
        pack(document, output=output, assets=assets_dir)

    assert not output.exists()


def test_pack_rejects_symlink_page_file(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_description_element_head.dclg"
    secret = tmp_path / "secret.png"
    secret.write_bytes(b"png")
    link = tmp_path / "1.png"
    link.symlink_to(secret)
    output = tmp_path / "symlink-page.dclx"

    with pytest.raises(PackagingError, match="symbolic link"):
        pack(document, output=output, pages=[link])

    assert not output.exists()


def test_pack_rejects_symlink_pages_directory(tmp_path: Path) -> None:
    document = VALID_DIR / "ok_description_element_head.dclg"
    real_pages = ARCHIVE_DEMO / "pages"
    pages_link = tmp_path / "pages"
    pages_link.symlink_to(real_pages)
    output = tmp_path / "symlink-pages-dir.dclx"

    with pytest.raises(PackagingError, match="symbolic link"):
        pack(document, output=output, pages=pages_link)

    assert not output.exists()
