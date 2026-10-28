#!/usr/bin/env python3
"""
Schema Snapshot Script for DocLang

Copies the development-head schemas (doclang/doclang.xsd, doclang/doclang.sch) to
doclang/schemas/<MAJOR.MINOR>/, the latest release of that spec minor version.

Usage:
    python utils/snapshot_schemas.py 0.8.0
"""

import argparse
import shutil
from pathlib import Path


def snapshot_schemas(version: str, project_root: Path | None = None) -> Path:
    """Copy the development-head schemas to doclang/schemas/<MAJOR.MINOR>/ (latest release of that minor)."""
    if project_root is None:
        project_root = Path(__file__).resolve().parent.parent

    major_minor = ".".join(version.split(".")[:2])
    package_dir = project_root / "doclang"
    target = package_dir / "schemas" / major_minor
    target.mkdir(parents=True, exist_ok=True)
    for name in ("doclang.xsd", "doclang.sch"):
        shutil.copyfile(package_dir / name, target / name)
    print(f"Snapshot schemas to {target}")
    return target


def main():
    parser = argparse.ArgumentParser(description="Snapshot the head schemas to doclang/schemas/<MAJOR.MINOR>/")
    parser.add_argument("version", help="Release version (e.g. 0.8.0)")
    args = parser.parse_args()
    snapshot_schemas(args.version)


if __name__ == "__main__":
    main()
