"""
Version resolution for the doclang package.

Release scripts resolve from git tags (only-version: tag → X.Y.Z; commits after →
X.Y.Z+g<sha>[.d<date> if dirty]). The CLI reads the installed package version via
importlib.metadata.
"""

import re
import subprocess
from datetime import date
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent

# git describe --long: v0.3.0 or v0.3.0-3-g93c2a53[-dirty]
_DESCRIBE_RE = re.compile(
    r"^(?:v)?(?P<tag>\d+\.\d+\.\d+)(?:-(?P<distance>\d+)-g(?P<node>[0-9a-f]+))?(?:-dirty)?$",
    re.IGNORECASE,
)


def version_from_describe(describe: str) -> str | None:
    """Map git describe output to setuptools-scm only-version format."""
    match = _DESCRIBE_RE.match(describe.strip())
    if not match:
        return None
    tag = match.group("tag")
    if match.group("distance") is None:
        return tag
    local = f"+g{match.group('node')}"
    if describe.rstrip().endswith("-dirty"):
        local += f".d{date.today().strftime('%Y%m%d')}"
    return f"{tag}{local}"


def version_from_git() -> str | None:
    """Resolve version from git tags."""
    try:
        describe = subprocess.run(
            ["git", "describe", "--dirty", "--tags", "--long"],
            cwd=_REPO_ROOT,
            capture_output=True,
            text=True,
            check=True,
            timeout=2,
        ).stdout
    except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
        return None
    return version_from_describe(describe)


def resolve_version() -> str:
    """Return the installed doclang distribution version."""
    try:
        return version("doclang")
    except PackageNotFoundError:
        return "unknown"


def release_version(version_str: str) -> str:
    """Strip PEP 440 local/dev/post suffixes; return MAJOR.MINOR[.PATCH]."""
    base = version_str.split("+", 1)[0]
    base = re.split(r"\.dev\d+", base, maxsplit=1)[0]
    base = re.split(r"\.post\d+", base, maxsplit=1)[0]
    return base


def release_version_triple(version_str: str) -> str:
    """Return MAJOR.MINOR.PATCH, padding PATCH with 0 when absent."""
    parts = release_version(version_str).split(".")
    while len(parts) < 3:
        parts.append("0")
    return ".".join(parts[:3])


def validate_version(version_str: str) -> bool:
    """True if version_str has at least MAJOR.MINOR release components."""
    parts = release_version(version_str).split(".")
    if len(parts) < 2 or len(parts) > 3:
        return False
    return all(part.isdigit() for part in parts)


def normalize_version(version_str: str) -> str:
    """Normalize and validate an explicit MAJOR.MINOR[.PATCH] version string."""
    normalized = release_version_triple(version_str.lstrip("v"))
    if not validate_version(normalized):
        raise ValueError(
            f"Invalid version format: '{version_str}' (expected MAJOR.MINOR or MAJOR.MINOR.PATCH, e.g. 0.4.0)"
        )
    return normalized
