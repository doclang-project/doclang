"""Migrate DocLang documents to another spec version."""

from doclang.migration._api import MigrationError, MigrationResult, migrate

__all__ = ["MigrationError", "MigrationResult", "migrate"]
