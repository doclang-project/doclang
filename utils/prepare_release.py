#!/usr/bin/env python3
"""
Prepare a DocLang Standard release.

Runs version sync, reference generation, ISO draft export, and CHANGELOG update.

Usage:
    uv run python utils/prepare_release.py 0.4.0
    uv run python utils/prepare_release.py v0.4.0 --reference-input reference/input
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from doclang.version import normalize_version

ROOT = Path(__file__).resolve().parent.parent
UTILS_DIR = Path(__file__).resolve().parent
if str(UTILS_DIR) not in sys.path:
    sys.path.insert(0, str(UTILS_DIR))

from generate_reference import generate_reference
from sync_version import sync_version
from write_iso_draft import write_iso_draft

DEFAULT_CHANGELOG = ROOT / "CHANGELOG.md"
DEFAULT_REFERENCE_INPUT = "reference/input"
GITHUB_REPO = "https://github.com/doclang-project/doclang-standard"


def get_latest_tag(project_root: Path) -> str | None:
    """Return the most recent tag reachable from HEAD, or None."""
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    tag = result.stdout.strip()
    return tag or None


def get_commits_since_tag(project_root: Path, tag: str | None) -> list[str]:
    """Return commit subjects since tag (or all commits)."""
    rev_range = f"{tag}..HEAD" if tag else "HEAD"
    try:
        result = subprocess.run(
            ["git", "log", rev_range, "--no-merges", "--pretty=format:%s"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return []

    return [line for line in result.stdout.splitlines() if line.strip()]


def build_changelog_section(
    version: str,
    project_root: Path,
    repo_url: str = GITHUB_REPO,
) -> str:
    """Build a new CHANGELOG section for the target release."""
    tag = f"v{version}"
    header = f"## [{tag}]({repo_url}/releases/tag/{tag})\n\n"

    latest_tag = get_latest_tag(project_root)
    if latest_tag == tag:
        # HEAD is exactly on the release tag; use the previous tag as the range base.
        try:
            result = subprocess.run(
                ["git", "describe", "--tags", "--abbrev=0", f"{tag}^"],
                cwd=project_root,
                capture_output=True,
                text=True,
                check=True,
            )
            latest_tag = result.stdout.strip() or None
        except (FileNotFoundError, subprocess.CalledProcessError):
            latest_tag = None

    subjects = get_commits_since_tag(project_root, latest_tag)
    if not subjects:
        return header + "* No commits since previous release.\n\n"

    entries = [f"* {subject}" for subject in subjects]
    return header + "\n".join(entries) + "\n\n"


def update_changelog(
    version: str,
    changelog_path: Path = DEFAULT_CHANGELOG,
    project_root: Path | None = None,
    repo_url: str = GITHUB_REPO,
) -> None:
    """Prepend a release section to CHANGELOG.md."""
    if project_root is None:
        project_root = ROOT

    section = build_changelog_section(version, project_root, repo_url=repo_url)
    existing = changelog_path.read_text(encoding="utf-8") if changelog_path.exists() else ""
    changelog_path.write_text(section + existing, encoding="utf-8")
    print(f"Updated {changelog_path}")


def prepare_release(
    version: str,
    reference_input: str = DEFAULT_REFERENCE_INPUT,
    project_root: Path | None = None,
) -> str:
    """Run the full release preparation workflow."""
    if project_root is None:
        project_root = ROOT

    normalized = normalize_version(version)
    print(f"Preparing release {normalized}...")

    sync_version(normalized, project_root=project_root)

    reference_dir = Path(reference_input)
    if not reference_dir.is_absolute():
        reference_dir = project_root / reference_dir
    generate_reference(reference_dir)

    write_iso_draft(project_root / "iso-standard.md")
    update_changelog(normalized, project_root=project_root)

    print(f"\nRelease {normalized} prepared.")
    print("Next steps:")
    print(f"  Once committed to 'main': tag commit as v{normalized}")
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Prepare a DocLang Standard release (sync, reference, ISO draft, changelog)",
    )
    parser.add_argument(
        "version",
        help="Target release version (e.g. 0.4.0 or v0.4.0)",
    )
    parser.add_argument(
        "--reference-input",
        default=DEFAULT_REFERENCE_INPUT,
        help=f"Directory with reference Excel and examples (default: {DEFAULT_REFERENCE_INPUT})",
    )
    args = parser.parse_args()

    try:
        prepare_release(args.version, reference_input=args.reference_input)
    except ValueError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except (FileNotFoundError, NotADirectoryError, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
