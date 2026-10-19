"""Tests for release preparation helpers."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from utils.rotate_migration_steps import rotate_migration_steps  # noqa: E402
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


def _project_with_next_step(tmp_path, schema_versions):
    migrate_dir = tmp_path / "doclang" / "migration" / "_steps"
    migrate_dir.mkdir(parents=True)
    # a copy of the real development step, so the rotation is exercised on realistic content
    (migrate_dir / "next.py").write_text(
        (ROOT / "doclang" / "migration" / "_steps" / "next.py").read_text(encoding="utf-8")
    )
    for version in schema_versions:
        (tmp_path / "doclang" / "schemas" / version).mkdir(parents=True)
    return migrate_dir


def test_rotate_renames_next_to_released_step_and_creates_a_fresh_one(tmp_path):
    migrate_dir = _project_with_next_step(tmp_path, ["0.6", "0.7"])
    original = (migrate_dir / "next.py").read_text(encoding="utf-8")

    released = rotate_migration_steps("0.8.2", tmp_path)

    assert released == migrate_dir / "v0_8_to_0_7.py"
    released_source = released.read_text(encoding="utf-8")
    assert released_source.startswith('"""Steps from spec version 0.8 to 0.7 (internal)."""')
    assert released_source.split('"""', 2)[2] == original.split('"""', 2)[2]  # same code, new docstring
    fresh = (migrate_dir / "next.py").read_text(encoding="utf-8")
    assert "def migrate(" in fresh and "_drop_tracks" not in fresh
    compile(released_source, "released", "exec")
    compile(fresh, "fresh", "exec")


def test_rotate_skips_patch_releases_and_first_versions(tmp_path):
    migrate_dir = _project_with_next_step(tmp_path, ["0.7", "0.8"])
    before = (migrate_dir / "next.py").read_text(encoding="utf-8")

    assert rotate_migration_steps("0.8.1", tmp_path) is None  # schemas/0.8 already exist: a patch release
    assert (migrate_dir / "next.py").read_text(encoding="utf-8") == before
    assert sorted(p.name for p in migrate_dir.iterdir()) == ["next.py"]

    assert rotate_migration_steps("0.7.0", tmp_path) is None  # nothing before 0.7
