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
    "<track>",
    "</track>",
    "<bdiv/>",
    "<cover>",
    "</cover>",
    "<frame>",
    "</frame>",
    "<audio>",
    "</audio>",
    "<voice>",
    "</voice>",
    "<chapter>",
    "</chapter>",
    '<hours value="',
    '<minutes value="',
    '<seconds value="',
    '<msecs value="',
)


def _location_tokens(resolution: int) -> list[str]:
    """Return one concrete ``<location value="N"/>`` token per value in ``[0, resolution)``."""
    return [f'<location value="{value}"/>' for value in range(resolution)]


def _hours_tokens() -> list[str]:
    """Return concrete ``<hours value="N"/>`` tokens for ``N`` in ``[0, 10)``."""
    return [f'<hours value="{value}"/>' for value in range(10)]


def _minutes_tokens() -> list[str]:
    """Return concrete ``<minutes value="N"/>`` tokens for ``N`` in ``[0, 60)``."""
    return [f'<minutes value="{value}"/>' for value in range(60)]


def _seconds_tokens() -> list[str]:
    """Return concrete ``<seconds value="N"/>`` tokens for ``N`` in ``[0, 60)``."""
    return [f'<seconds value="{value}"/>' for value in range(60)]


def _msecs_tokens() -> list[str]:
    """Return concrete ``<msecs value="N"/>`` tokens for ``N`` in ``{0, 10, 20, ..., 990}``."""
    return [f'<msecs value="{value}"/>' for value in range(0, 1000, 10)]


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
    return [
        *_FIXED_TOKENS,
        *_location_tokens(max_resolution),
        *_hours_tokens(),
        *_minutes_tokens(),
        *_seconds_tokens(),
        *_msecs_tokens(),
    ]
