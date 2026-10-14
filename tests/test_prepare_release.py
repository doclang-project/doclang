"""Tests for release preparation helpers."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.snapshot_schemas import snapshot_schemas  # noqa: E402


def test_snapshot_schemas_copies_head_to_minor_folder(tmp_path):
    package_dir = tmp_path / "doclang"
    package_dir.mkdir()
    (package_dir / "doclang.xsd").write_text("xsd", encoding="utf-8")
    (package_dir / "doclang.sch").write_text("sch", encoding="utf-8")

    target = snapshot_schemas("0.8.3", tmp_path)

    assert target == package_dir / "schemas" / "0.8"
    assert (target / "doclang.xsd").read_text(encoding="utf-8") == "xsd"
    assert (target / "doclang.sch").read_text(encoding="utf-8") == "sch"
