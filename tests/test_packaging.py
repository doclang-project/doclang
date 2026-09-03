"""Tests for DocLang archive packaging."""

from __future__ import annotations

import zipfile
from pathlib import Path

import pytest

from doclang import PackagingError, ValidationError, pack

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
