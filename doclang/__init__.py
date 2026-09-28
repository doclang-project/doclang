"""DocLang reference validator."""

from doclang._native import DoclangDocument, DocLangXDocument
from doclang.validation import ValidationError, validate

DoclangXDocument = DocLangXDocument

__all__ = ["DocLangXDocument", "DoclangDocument", "DoclangXDocument", "ValidationError", "validate"]
