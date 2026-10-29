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


def _project_with_steps(tmp_path, schema_versions):
    migrate_dir = tmp_path / "doclang" / "migration" / "_steps"
    migrate_dir.mkdir(parents=True)
    # a copy of the real development step, so the rotation is exercised on realistic content
    (migrate_dir / "from_next.py").write_text(
        (ROOT / "doclang" / "migration" / "_steps" / "from_next.py").read_text(encoding="utf-8")
    )
    for version in schema_versions:
        (tmp_path / "doclang" / "schemas" / version).mkdir(parents=True)
    return migrate_dir


def test_rotate_renames_next_to_released_step_and_creates_a_fresh_one(tmp_path):
    migrate_dir = _project_with_steps(tmp_path, ["0.6", "0.7"])
    original = (migrate_dir / "from_next.py").read_text(encoding="utf-8")

    released = rotate_migration_steps("0.8.2", tmp_path)

    assert released == migrate_dir / "v0_8_to_0_7.py"
    released_source = released.read_text(encoding="utf-8")
    assert released_source.startswith('"""Steps from spec version 0.8 to 0.7 (internal)."""')
    assert released_source.split('"""', 2)[2] == original.split('"""', 2)[2]  # same code, new docstring
    fresh = (migrate_dir / "from_next.py").read_text(encoding="utf-8")
    assert "def migrate(" in fresh and "_drop_tracks" not in fresh
    compile(released_source, "released", "exec")
    compile(fresh, "fresh", "exec")


def test_rotate_renames_to_next_to_released_up_step(tmp_path):
    migrate_dir = _project_with_steps(tmp_path, ["0.7"])
    to_next = (ROOT / "doclang" / "migration" / "_steps" / "to_next.py").read_text(encoding="utf-8")
    (migrate_dir / "to_next.py").write_text(to_next, encoding="utf-8")

    rotate_migration_steps("0.8.0", tmp_path)

    released = (migrate_dir / "v0_7_to_0_8.py").read_text(encoding="utf-8")
    assert released.startswith('"""Steps from spec version 0.7 to 0.8 (internal)."""')
    assert released.split('"""', 2)[2] == to_next.split('"""', 2)[2]
    fresh = (migrate_dir / "to_next.py").read_text(encoding="utf-8")
    assert "def migrate(" in fresh and "No rules yet" in fresh
    compile(fresh, "fresh", "exec")
    assert sorted(p.name for p in migrate_dir.iterdir()) == [
        "from_next.py",
        "to_next.py",
        "v0_7_to_0_8.py",
        "v0_8_to_0_7.py",
    ]


def test_rotate_skips_patch_releases_and_first_versions(tmp_path):
    migrate_dir = _project_with_steps(tmp_path, ["0.7", "0.8"])
    before = (migrate_dir / "from_next.py").read_text(encoding="utf-8")

    assert rotate_migration_steps("0.8.1", tmp_path) is None  # schemas/0.8 already exist: a patch release
    assert (migrate_dir / "from_next.py").read_text(encoding="utf-8") == before
    assert sorted(p.name for p in migrate_dir.iterdir()) == ["from_next.py"]

    assert rotate_migration_steps("0.7.0", tmp_path) is None  # nothing before 0.7


def test_released_steps_migrate_as_the_development_steps_did(tmp_path, monkeypatch):
    """Simulate the release of the head: the rotated steps load with the same versions and directions, and migrate
    the file-based cases exactly as before."""
    import shutil

    import pytest
    from lxml import etree

    from doclang._schemas import _available_versions, _version_key
    from doclang.migration import _steps as steps_package
    from doclang.migration._api import _head_version
    from doclang.migration._plan import _load_steps, _plan
    from doclang.migration._tree import Changes

    newest = max(_available_versions(), key=_version_key)
    head = _head_version(newest)
    if head is None:
        pytest.skip("the development head has no changes of its own")
    before = _load_steps(newest, head)

    steps_dir = tmp_path / "doclang" / "migration" / "_steps"
    shutil.copytree(ROOT / "doclang" / "migration" / "_steps", steps_dir, ignore=shutil.ignore_patterns("__pycache__"))
    for version in _available_versions():
        (tmp_path / "doclang" / "schemas" / version).mkdir(parents=True)
    rotate_migration_steps(f"{head}.0", tmp_path)

    monkeypatch.setattr(steps_package, "__path__", [str(steps_dir)])
    for name in [n for n in sys.modules if n.startswith(f"{steps_package.__name__}.")]:
        monkeypatch.delitem(sys.modules, name)  # import the rotated modules, not the cached ones
    after = _load_steps(head, None)  # right after the release, the head has no changes of its own

    assert sorted((s.source, s.target) for s in after) == sorted((s.source, s.target) for s in before)

    def migrated(source_file, target, steps):
        root = etree.parse(str(source_file)).getroot()
        for step in _plan(root.get("version"), target, steps):
            step.apply(root, Changes())
        return etree.tostring(root)

    cases = sorted((ROOT / "tests" / "data" / "migration").glob("*/*in.dclg"))
    assert cases
    for case in cases:
        target = case.parent.name.split("_to_")[1]
        assert migrated(case, target, after) == migrated(case, target, before), case.name
