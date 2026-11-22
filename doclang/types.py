"""Typed records returned by the native DocLang package and traversal APIs."""

from __future__ import annotations

from typing import TypedDict


class DoclangNodeRecord(TypedDict):
    xpath: str
    parent_xpath: str
    name: str
    text: str
    truncated: bool
    page: int
    bbox: tuple[tuple[float, float], tuple[float, float]] | None


class PackageIssue(TypedDict):
    code: str
    path: str
    message: str


class PackageReport(TypedDict):
    ok: bool
    errors: list[PackageIssue]
