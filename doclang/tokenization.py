"""DocLang special-token vocabulary, per spec.md's (non-normative) "Token vocabulary" recommendation."""

from __future__ import annotations

DEFAULT_MAX_RESOLUTION = 512

_HEADING_LEVELS = range(2, 7)
_FIELD_HEADING_LEVELS = range(2, 7)

_FIXED_TOKENS: tuple[str, ...] = (
    "<doclang>",
    "</doclang>",
    "<page_break/>",
    '"/>',
    "<text>",
    "</text>",
    "<heading>",
    *(f'<heading level="{level}">' for level in _HEADING_LEVELS),
    "</heading>",
    "<footnote>",
    "</footnote>",
    "<page_header>",
    "</page_header>",
    "<page_footer>",
    "</page_footer>",
    "<field_region>",
    "</field_region>",
    "<list>",
    '<list class="ordered">',
    "</list>",
    "<table>",
    "</table>",
    "<index>",
    "</index>",
    "<formula>",
    "</formula>",
    '<code><label value="',
    "</code>",
    '<picture><label value="',
    '<picture class="chart"><label value="',
    "</picture>",
    "<marker>",
    "</marker>",
    "<group>",
    "</group>",
    "<field_heading>",
    *(f'<field_heading level="{level}">' for level in _FIELD_HEADING_LEVELS),
    "</field_heading>",
    "<field_item>",
    "</field_item>",
    "<key>",
    "</key>",
    "<value>",
    '<value class="fillable">',
    "</value>",
    "<hint>",
    "</hint>",
    "<caption>",
    "</caption>",
    "<description>",
    "</description>",
    "<summary>",
    "</summary>",
    '<thread thread_id="',
    '<xref thread_id="',
    '<href uri="',
    "<custom>",
    "</custom>",
    '<layer value="',
    '<src uri="',
    "<tabular>",
    "</tabular>",
    '<checkbox class="unselected"/>',
    '<checkbox class="selected"/>',
    "<content>",
    "</content>",
    "<![CDATA[",
    "]]>",
    "<bold>",
    "</bold>",
    "<italic>",
    "</italic>",
    "<underline>",
    "</underline>",
    "<strikethrough>",
    "</strikethrough>",
    "<superscript>",
    "</superscript>",
    "<subscript>",
    "</subscript>",
    "<handwriting>",
    "</handwriting>",
    "<rtl>",
    "</rtl>",
    "<fcel/>",
    "<ecel/>",
    "<ched/>",
    "<rhed/>",
    "<corn/>",
    "<srow/>",
    "<lcel/>",
    "<ucel/>",
    "<xcel/>",
    "<nl/>",
    "<ldiv/>",
    "<ldiv><marker>",
    "</marker></ldiv>",
)


def _location_tokens(resolution: int) -> list[str]:
    """Return one concrete ``<location value="N"/>`` token per value in ``[0, resolution)``."""
    return [f'<location value="{value}"/>' for value in range(resolution)]


def get_special_tokens(*, max_resolution: int = DEFAULT_MAX_RESOLUTION) -> list[str]:
    """
    Return the DocLang special-token vocabulary as a flat list of token strings.

    This implements spec.md's "Token vocabulary" table, which is non-normative guidance
    (the spec's "Recommendations" appendix) -- one reasonable tokenization, not a
    conformance requirement other DocLang tools are bound to.

    ``max_resolution`` should be the largest ``location@resolution`` (i.e.
    ``default_resolution@width``/``@height``, or a per-``<location>`` override) used across your
    documents; pass the larger of your x/y resolutions if they differ.
    """
    return [*_FIXED_TOKENS, *_location_tokens(max_resolution)]
