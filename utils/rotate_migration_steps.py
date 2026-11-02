#!/usr/bin/env python3
"""
Migration Step Rotation Script for DocLang

When a release introduces a new spec minor version, turns the development steps into the released steps
for it, and creates fresh, empty ones:
- doclang/migration/_steps/from_next.py -> v<NEW>_to_<PREVIOUS>.py (e.g. v0_8_to_0_7.py), down
- doclang/migration/_steps/to_next.py -> v<PREVIOUS>_to_<NEW>.py (e.g. v0_8_to_0_9.py), up
<PREVIOUS> is the newest minor with schemas in doclang/schemas/.
Tests that import a development step (``from doclang.migration._steps import to_next``) are retargeted to the
released one, so they keep testing the rules they were written for.
Nothing happens for a patch release of an existing minor, or if there is no previous minor.

Run this before utils/snapshot_schemas.py, which creates doclang/schemas/<NEW>/.

Usage:
    python utils/rotate_migration_steps.py 0.8.0
"""

import argparse
import re
from pathlib import Path

_FRESH_FROM_NEXT = '''"""Steps from the development head to the newest released spec version (internal).

Every addition to the head schema that the previous version cannot express adds its rule here.
At release, ``utils/prepare_release.py`` renames this module to ``v<new>_to_<previous>.py`` and
creates a fresh, empty one. Do not mention version numbers in the messages for that reason.
"""

from __future__ import annotations

from lxml import etree

from doclang.migration._tree import Changes


def migrate(root: etree._Element, changes: Changes) -> None:
    """No rules yet."""
'''

_FRESH_TO_NEXT = '''"""Steps from the newest released spec version to the development head (internal).

Every change in the head that gives existing documents a different meaning adds its rule here, rewriting the
document so that it keeps the meaning it had. At release, ``utils/prepare_release.py`` renames this module to
``v<previous>_to_<new>.py`` and creates a fresh, empty one. Do not mention version numbers in the messages for
that reason.
"""

from __future__ import annotations

from lxml import etree

from doclang.migration._tree import Changes


def migrate(root: etree._Element, changes: Changes) -> None:
    """No rules yet."""
'''


def _key(version: str) -> tuple[int, int]:
    major, minor = version.split(".")
    return int(major), int(minor)


def rotate_migration_steps(version: str, project_root: Path | None = None) -> Path | None:
    """Rotate from_next.py and to_next.py for a release of ``version``; returns the released down step's path, or None
    if skipped."""
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent

    new = ".".join(version.split(".")[:2])
    package_dir = project_root / "doclang"
    schemas_dir = package_dir / "schemas"
    from_next_path = package_dir / "migration" / "_steps" / "from_next.py"

    if (schemas_dir / new).exists():
        print(f"Schemas for {new} already exist: not rotating migration steps")
        return None
    previous_versions = (
        [e.name for e in schemas_dir.iterdir() if re.fullmatch(r"\d+\.\d+", e.name) and _key(e.name) < _key(new)]
        if schemas_dir.is_dir()
        else []
    )
    if not previous_versions:
        print(f"No version before {new} has schemas: not rotating migration steps")
        return None
    previous = max(previous_versions, key=_key)

    released = _rotate(from_next_path, new, previous, _FRESH_FROM_NEXT)
    renames = {"from_next": released.stem}
    to_next_path = from_next_path.with_name("to_next.py")
    if to_next_path.exists():
        renames["to_next"] = _rotate(to_next_path, previous, new, _FRESH_TO_NEXT).stem
    _retarget_tests(project_root / "tests", renames)
    return released


def _rotate(path: Path, source: str, target: str, fresh: str) -> Path:
    """Rename the development step ``path`` to the released step from ``source`` to ``target``."""
    released = path.with_name(f"v{source.replace('.', '_')}_to_{target.replace('.', '_')}.py")
    content = path.read_text(encoding="utf-8")
    content = re.sub(
        r'^""".*?"""',
        f'"""Steps from spec version {source} to {target} (internal)."""',
        content,
        count=1,
        flags=re.DOTALL,
    )
    released.write_text(content, encoding="utf-8")
    path.write_text(fresh, encoding="utf-8")
    print(f"Migration steps rotated: {path.name} -> {released.name}")
    return released


def _retarget_tests(tests_dir: Path, renames: dict[str, str]) -> None:
    """In the tests importing a development step, refer to the released step instead."""
    if not tests_dir.is_dir():
        return
    imports = re.compile(r"^\s*from doclang\.migration\._steps import (" + "|".join(renames) + r")\b", re.MULTILINE)
    names = re.compile(r"\b(" + "|".join(renames) + r")\b")
    for path in sorted(tests_dir.rglob("*.py")):
        content = path.read_text(encoding="utf-8")
        if imports.search(content):
            path.write_text(names.sub(lambda m: renames[m.group(1)], content), encoding="utf-8")
            print(f"Tests retargeted to the released migration steps: {path.name}")


def main():
    parser = argparse.ArgumentParser(description="Rotate the development migration steps for a release")
    parser.add_argument("version", help="Release version (e.g. 0.8.0)")
    args = parser.parse_args()
    rotate_migration_steps(args.version)


if __name__ == "__main__":
    main()
