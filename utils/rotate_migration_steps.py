#!/usr/bin/env python3
"""
Migration Step Rotation Script for DocLang

When a release introduces a new spec minor version, turns the development steps into the released step
for it: doclang/migration/_steps/next.py -> doclang/migration/_steps/v<NEW>_to_<PREVIOUS>.py (e.g. v0_8_to_0_7.py),
and creates a fresh, empty next.py. <PREVIOUS> is the newest minor with schemas in doclang/schemas/.
Nothing happens for a patch release of an existing minor, or if there is no previous minor.

Run this before utils/snapshot_schemas.py, which creates doclang/schemas/<NEW>/.

Usage:
    python utils/rotate_migration_steps.py 0.8.0
"""

import argparse
import re
from pathlib import Path

_FRESH_NEXT = '''"""Steps from the development head to the newest released spec version (internal).

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


def _key(version: str) -> tuple[int, int]:
    major, minor = version.split(".")
    return int(major), int(minor)


def rotate_migration_steps(version: str, project_root: Path | None = None) -> Path | None:
    """Rotate next.py for a release of ``version``; returns the released step's path, or None if skipped."""
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent

    new = ".".join(version.split(".")[:2])
    package_dir = project_root / "doclang"
    schemas_dir = package_dir / "schemas"
    next_path = package_dir / "migration" / "_steps" / "next.py"

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

    released = next_path.with_name(f"v{new.replace('.', '_')}_to_{previous.replace('.', '_')}.py")
    content = next_path.read_text(encoding="utf-8")
    content = re.sub(
        r'^""".*?"""',
        f'"""Steps from spec version {new} to {previous} (internal)."""',
        content,
        count=1,
        flags=re.DOTALL,
    )
    released.write_text(content, encoding="utf-8")
    next_path.write_text(_FRESH_NEXT, encoding="utf-8")
    print(f"Migration steps rotated: next.py -> {released.name}")
    return released


def main():
    parser = argparse.ArgumentParser(description="Rotate doclang/migration/_steps/next.py for a release")
    parser.add_argument("version", help="Release version (e.g. 0.8.0)")
    args = parser.parse_args()
    rotate_migration_steps(args.version)


if __name__ == "__main__":
    main()
