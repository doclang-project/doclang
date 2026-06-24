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
