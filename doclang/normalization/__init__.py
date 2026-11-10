"""Normalize super/subscripts, symbols and inline math to the representation recommended by the specification."""

from doclang.normalization._api import NormalizationError, NormalizationResult, normalize, rules

__all__ = ["NormalizationError", "NormalizationResult", "normalize", "rules"]
