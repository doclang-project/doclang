# ISO XXX - DocLang: Universal Document Markup Format (Revised)

## Foreword

This document was prepared by

| Name | Company | Email |
|------|---------|-------|
| Peter Staar | IBM | taa@zurich.ibm.com |
| Panos Vagenas | IBM | pva@zurich.ibm.com |
| Maksym Lysak | IBM | mly@zurich.ibm.com |
| Nikolaos Livathinos | IBM | nli@zurich.ibm.com |
| Christoph Auer | IBM | cau@zurich.ibm.com |
| Michele Dolfi | IBM | dol@zurich.ibm.com |
| Said Gürbüz | IBM | Said.Gurbuz@ibm.com |
| Marlene Wolfgruber | ABBY | marlene.wolfgruber@abbyy.com |
| Maxime Vermeir | ABBY | maxime.vermeir@abbyy.com |
| Morgan Logue | ABBY | morgan.logue@abbyy.com |
| Andrew Pery | ABBY | ??? |
| Christopher Giblin | IBM | cgi@zurich.ibm.com|
| Jehlum Vitasta Pandit | RedHat | jepandit@redhat.com |
| Ali Maredia | RedHat | amaredia@redhat.com |
| Santosh Borse | IBM | ssborse@us.ibm.com |
| Yousaf Shah | IBM | syshah@us.ibm.com |
| Maroun Touma | IBM | touma@us.ibm.com |

This International Standard specifies the DocLang format, a universal markup language for representing structured document content with semantic, geometric, and formatting information.

## Introduction

The proliferation of digital documents across diverse formats (PDF, HTML, Word, etc.) has created significant challenges in document processing, conversion, and understanding. These were mainly designed for efficient rendering and often result in loss of semantic information, structural relationships, or geometric context during document conversion.

DocLang addresses these challenges by providing a minimalist, unambiguous markup format that:

- Preserves complete document structure and semantics
- Maintains geometric and layout information when appropriate
- Supports complex document components including tables, formulas, code, nested lists, and charts
- Enables lossless round-trip conversion between formats regarding content
- Maintains token efficiency by defining controlled vocabulary of tags and attributes
- Eliminates ambiguity by enforcing a well defined set of tags with restricted, non generic usage ( and preserves semantic clarity )

This standard builds upon research in document understanding and is intended to represent the content of a document as accurately as possible while maintaining implementation simplicity.

## Scope

This standard specifies:

- The syntax and semantics of the DocLang markup language
- Rules for encoding document structure, content, and metadata
- Primitives for representing geometric layout and pagination
- Methods for expressing formatting and text direction
- Specifications for complex document components (tables, charts, formulas, code, forms)
- Requirements for conforming implementations

## Motivation

The motivation for this new markup language is twofold,

1. It is created from the ground up to be able to represent complex, multimodal content with visual grounding in plain text with markup
2. It is created with the express purpose to be compatible with LLM tokenizers, i.e. use a markup structure that maps naturally (== a 1-to-1 mapping between DocLang tokens and LLM tokens) and efficiently (== minimal token count).

As a consequence of point 2, this standard ensures that there is a limited number or tags and attributes. In general, we intend that the number of syntax tokens should not exceed 1000. The latter is not a strong bound, but rather a direction.

There is an exception for meta-data markup. Meta-data is not intended to be used or produced by LLMs, so it is in general possible to include an expanded set of protected markup tokens. Nevertheless, we do want to normalize as much as possible this representation.

Such requirements preclude us from using existing markup languages such as Markdown (incomplete scope), HTML (not concise enough), LaTeX (ambiguity of representation) etc.

<figure style="text-align: left">
    <img src="resources/html_v_otsl.png"
         alt="HTML vs OTSL" style="width:700px">
    <figcaption>Example in pure table structure representation, omitting content of cells, when comparing HTML to DocLang (OTSL tags). HTML sequence is both longer and uses more tokens than DocLang/OTSL</figcaption>
</figure>

<!-- TODO: update image text for DocLang: replace <section> with <heading>, add CDATA in <code> -->
<figure style="text-align: left">
    <img src="resources/doclang_example.png"
         alt="HTML vs OTSL" style="width:1000px">
    <figcaption>Examples of real-world document fragments and their DocLang representation</figcaption>
</figure>

A specific class of related formats is the one operating on the OCR level, including [PageXML](https://github.com/PRImA-Research-Lab/PAGE-XML), [ALTO XML](https://github.com/altoxml), and [hOCR](https://github.com/kba/hocr-spec).

Beyond certain low-level similarities (e.g. presence of bounding box information), the DocLang format is significantly differentiated as it is designed to be AI-native:

- The above-mentioned formats focus on OCR processing, e.g. for archives, browser display, or other types of OCR/HTR pipelines, while DocLang is designed for LLM/VLM generation, with token efficiency in mind.
- Whereas these formats are primarily concerned with the geometric locations of the various spans of text, DocLang also places a strong focus on the semantic meaning and internal structure of the involved complex components, providing various native elements for headings, formulas, code, etc. and also rich table structure support (incl. table headings, spanned cells, etc.), this way capturing richer context for generative AI applications to leverage.

## Terminology

Abstract concepts:

- **document component**: A cohesive and meaningful part of the document, e.g. a table, list item with a marker, a bold piece of text, etc.

Adopted from XML:

- **element**: An XML element.
- **attribute**: An XML attribute.
- **tag**: An XML tag: can be a start-tag, an end-tag, or an empty-element tag (a.k.a. self-closing tag).

Adopted from HTML:

- **block-level element**: An element that is meant to be interpreted or displayed as a block, i.e. starting on a new line and occupying the full width of its container; a typical HTML example is the `p` element (paragraph).
- **inline element**: An element that can be used within block element to shape its in-line structure; a typical HTML example is the `span` element.

Native to DocLang:

- **(DocLang) token**: A low-level symbol capturing some aspect of a document or of a component thereof, expressed as a tag.

<!-- for internal use:
Docling:
- **DoclingDocument**: The Python class used in Docling to represent a document
- **(DoclingDocument) item**: Building block of a DoclingDocument; an item typically corresponds to a document component.
- **(DoclingDocument) inline group**: A grouping of DoclingDocument items that are meant to be interpreted as a single
  unit of text, i.e. without line breaks or vertical space between them.
-->

## Property Semantics

In XML, the attribute syntax allows explicitly separating an element's properties from its content.
Let's consider the following example: `<elem size="250" color="#ffeedd">foo</elem>`.
This denotes an `elem` element, including its properties (`size` and `color`) and its content (`foo`).

For an element with multiple possible property values, the attribute syntax can lead to an increased complexity of the respective possible tokenized representations.
For instance, the following could all be valid variants of an `elem` start tag: `<elem size="300" color="#aabbcc">`, `<elem size="42">`, `<elem color="#112233">`, `<elem>`.

Aiming at LLM-friendliness, in such cases, the ISO DocLang format favors an alternative representation of property semantics, namely captured as respective elements leading the content.
The example above could be represented as `<elem><size>250</size><color>#ffeedd</color>foo</elem>`. Depending on the specific properties, self-closing elements are used too.

This representation can reduce the number of tokens, making it easier for language models to learn and predict.

For elements with a strictly limited set of possible property values, attributes are still used.

## Content encoding

The content of the elements is encoded according to the following rules:

- unicode textual content is encoded as utf-8.
- special characters reserved by XML, such as `<` (complete list defined in Appendix B), can be represented:
  - either by escaping with the respective XML entities, e.g. `<` becomes `&lt;`,
  - or using the CDATA section syntax, e.g. raw text `<foo>` can be represented as `<![CDATA[<foo>]]>`

## DocLang Structure

DocLang is a constrained subset of XML with the following characteristics:

- Simplified syntax with a finite set of allowed tags
- Constrained use of attributes on most elements
- Character-based encoding using legal Unicode characters (except Null)
- Standard XML parsing rules apply for markup vs content distinction

DocLang defines the following categories of elements:

- **special**: Elements that establish document scope and pagination, such as `doclang`, `page_break`, and `time_break`.
- **provenance**: Elements that can provide visual or time grounding. The visual grounding is necessary for documents with pagination, the temporal grounding is necessary for audio based documents (music and movies).
  - **geometric**: Elements that capture geometric position as normalized coordinates/bounding boxes (via repeated `location`) anchoring block-level content to the page.
  - **time**: Elements that capture temporal positions using `<hour value={integer}/><minute value={integer}/><second value={integer}/><centisecond value={integer}/>` for a timestamp and a double timestamp for time intervals.
- **semantic**: Block-level elements that convey document meaning (e.g., titles, paragraphs, captions, lists, forms, tables, formulas, code, pictures), optionally preceded by location tokens.
- **formatting**: Inline elements that modify textual presentation within semantic content (e.g., `bold`, `italic`, `strikethrough`, `superscript`, `subscript`, `rtl`, `inline class="formula|code|picture"`, `br`).
- **grouping**: Elements that organize semantic blocks into logical hierarchies and composites (e.g., `list`, `group type=*`) and never carry location tokens.
- **structural**: Sequence tokens that define internal structure for complex constructs (primarily OTSL table layout: `otsl`, `fcel`, `ecel`, `lcel`, `ucel`, `xcel`, `nl`, `ched`, `rhed`, `corn`, `srow`; and field parts like `key`/`value`).
- **content**: Lightweight content helpers used inside semantic blocks for explicit payload and annotations (e.g., `marker`, `checkbox`).
- **binary data**: Elements that embed or reference non-text payloads for media—either inline as `base64` or via `uri`—allowed under `picture`, `inline class="picture"`, or at page level.
- **metadata**: Elements that provide metadata about the document or its components, contained within `head` and `meta` respectively.
- **continuation** tokens: Markers that indicate content spanning pages or table boundaries (e.g., `thread`, `h_thread`, each with a required `id` attribute) to stitch split content (e.g., across columns or pages).

### Special Elements

These elements have a specific purpose in defining the high-level structure of the document.

#### The `doclang` Element

Every DocLang document is wrapped in a `<doclang>` root element.

Here is an example:

```xml
<doclang>
  <!-- rest of the document -->
</doclang>
```

#### The `version` Attribute

The `doclang` root element MAY carry an optional `version` attribute following Semantic Versioning (MAJOR.MINOR.PATCH).
When no version is specified, the default is `1.0.0`.

Example:

```xml
<doclang version="1.0.0">
  <!-- rest of the document -->
</doclang>
```

#### The `page_break` Element

A paginated document may be divided into pages using the `<page_break/>` empty-element tag.

Here is an example:

```xml
<doclang>
  <!-- first page content -->
  <page_break/>
  <!-- second page content -->
</doclang>
```

The content between two `<page_break/>` is in itself a DocLang document, if it is sandwiched between `<doclang>...</doclang>`.

#### The `time_break` Element

Audio-based documents may be divided into timed segments. These timed segments can be indicated by the `<time_break/>` symbol.

```xml
<doclang>
  <!-- first page content -->
  <time_break/>
  <!-- second page content -->
</doclang>
```

The content between two `<time_break/>` is in itself a DocLang document, if it is sandwiched between `<doclang>...</doclang>`.

### Provenance Elements

#### The `location` Element

The `location` element represents geometric information with value (and optional resolution) attributes of the format `<location value="integer" resolution="integer"/>` with 0 <= value <= resolution.

- Single coordinate at (100, 200): `<location value="100"/><location value="200"/>`
- Bounding box with (x0, y0) = (100, 200) and (x1, y1) = (300, 400): `<location value="100"/><location value="200"/><location value="300"/><location value="400"/>`

Coordinate system and encoding rules:

- Origin: The origin of the coordinate system is the bottom-left corner of the page.
- Point: Use exactly 2 consecutive `location` tokens to encode a point; the first token is x, the second is y.
- Bounding box: Use exactly 4 consecutive `location` tokens to encode a bounding box in strict order: x0, y0, x1, y1.
- Rotated rectangle: Use exactly 8 consecutive `location` tokens to encode a (potentially rotated) rectangle in strict order: x0, y0, x1, y1, x2, y2, x3, y3; x0, y0 and x1, y1 lie along the bottom edge in reading order.
- Normalization: Each `location`’s `value` is an integer in `[0, resolution]`; if a `location` specifies a `resolution` attribute it is used for that token, otherwise the `head.default_resolution` applies. When neither is available, use `512×512` as the implicit default.
- Connection to page size: The boxes are proportional to the page where they belong, they will not capture the actual size or aspect ratio. Those can be reconstructed with the `page_size` metadata.

The `location` element may only be used in elements which are meant to be interpreted as block-level, as specified further below.

Usage examples:

```xml
<!-- Bounding box on a title -->
<heading level="1">
  <location value="50"/><location value="310"/>
  <location value="450"/><location value="340"/>
  Annual Report
</heading>

<!-- Paragraph anchored by a bounding box -->
<text>
  <location value="60"/><location value="260"/>
  <location value="440"/><location value="270"/>
  This paragraph is spatially anchored on the page.
</text>

<!-- Picture with 8-point rotated rectangle -->
<picture>
  <location value="200"/><location value="200"/>
  <location value="400"/><location value="180"/>
  <location value="420"/><location value="380"/>
  <location value="220"/><location value="400"/>
  <uri>assets/fig2.png</uri>
  <caption>Figure 2: Rotated component</caption>
</picture>

<!-- Mixed per-token resolution overriding default -->
<text>
  <location value="100" resolution="1000"/>
  <location value="200" resolution="1000"/>
  <location value="900" resolution="1000"/>
  <location value="800" resolution="1000"/>
  Coordinates expressed in a 1000×1000 grid.
</text>
```

#### The `timestamp` Element

The `timestamp` element represents temporal provenance using four self-closing tokens:
`<hour value="integer"/>`, `<minute value="integer"/>`, `<second value="integer"/>` and `<centisecond value="integer"/>`, where the first 3 tokens are compulsory and the last one is optional.

- Point in time with second-level precision: Use 3 consecutive tokens to encode a single timestamp in strict order: hour, minute, second.
- Point in time with sub-second precision: Use 4 consecutive tokens to encode a single timestamp in strict order: hour, minute, second, centisecond.
- Time interval with second-level precision: Use exactly 6 consecutive tokens to encode a range: first the start timestamp (hour, minute, second), then the end timestamp (hour, minute, second).
- Time interval with sub-second precision: Use exactly 8 consecutive tokens to encode a range: first the start timestamp (hour, minute, second, centisecond), then the end timestamp (hour, minute, second, centisecond).

Examples:

- Single timestamp at 0:01:23: `<hour value="0"/><minute value="1"/><second value="23"/>`
- Single timestamp with sub-second precision at 12:34:56.12: `<hour value="12"/><minute value="34"/><second value="56"/><centisecond value="12"/>`
- Interval from 00:00:10 to 00:01:05:
  `<hour value="0"/><minute value="0"/><second value="10"/><hour value="0"/><minute value="1"/><second value="5"/>`
- Interval with sub-second precision from 01:20:00.0 to 02:05:30.67:
  `<hour value="1"/><minute value="20"/><second value="0"/><centisecond value="0"/><hour value="2"/><minute value="5"/><second value="30.123"/><centisecond value="67"/>`

Encoding rules:

- Ordering: The token order is strictly `hour`, then `minute`, then `second`, then `centisecond`; for intervals, emit start triplet first, then end triplet. In case of sub-second timestamps use a quadruplet in the order `hour`, then `minute`, then `second`, then `centisecond`; for internals with sub-second precison use 2 quadruplets, first the start quadruplet and then the end quadruplet.
- Ranges: `hour.value` is an integer in `[0, 99]`; `minute.value` is an integer in `[0, 59]`; `second.value` is an integer in `[0, 59]`; `centisecond.value` is an integer in `[0, 99]`.
- Normalization: Out-of-range carry is not allowed. Producers MUST pre-normalize (e.g., 0h 61m 5s must be encoded as 1h 1m 5s).
- Monotonicity (intervals): The end timestamp MUST represent a time that is greater than or equal to the start timestamp when converted to total seconds. Equal start and end encodes a zero-length anchor.
- Placement: Timestamp tokens MAY only be used on elements intended to be interpreted as block-level (see Semantic Elements). When present, they MUST precede the element’s textual content and any inline formatting tokens.
- Coexistence with location: When both geometric `location` tokens and `timestamp` tokens are present, both sets MUST appear before content. The relative order between geometric and temporal tokens has no semantic impact; serializers SHOULD use a consistent order.
- Interpretation: Timestamps are relative to the media’s timeline (e.g., an audio/video track or timed transcript) and are not wall-clock times; time zones and dates do not apply.

Usage examples:

```xml
<text>
  <hour value="0"/><minute value="2"/><second value="15"/>
  Speaker starts the introduction.
  <br/>
  Main points follow.
  <br/>
  Conclusion.
  <br/>
</text>

<text>
  <hour value="0"/><minute value="5"/><second value="0"/><centisecond value="72"/>
  <hour value="0"/><minute value="6"/><second value="30"/><centisecond value="15"/>
  Applause segment
</text>
```

### Semantic Elements

Semantic elements represent semantic blocks of the document and are meant to be interpreted as block-level elements.
Each semantic element may begin with a bounding box, capturing the element's bounding box.

| Element | Description |
|-------|-------------|
| `title` | Document title |
| `heading` | Section header, with optional level N ≥ 1 |
| `text` | Generic text content |  <!--  TODO: rename to `paragraph` -->
| `caption` | Caption for floating elements |
| `footnote` | Footnote content |
| `page_header` | Page header content |
| `page_footer` | Page footer content |
| `watermark` | Page contains watermark | <!-- watermark can be text or image - do we want to capture that? also do we want to know if watermark is in background or overlay?-->
| `list_text` | Leading text of a list item, including any available marker or checkbox information |
| `field_item` | Field item container with optional key and multiple values |
| `field_region` | Field region container with one or more field items |
| `field_heading` | Field heading within a field region, with optional level N ≥ 1 |
| `key` | Key of the field item: can be a descendant of `field_item` |
| `value` | Value of the field item: can be a descendant of `field_item`; optional `class` attribute with values `read_only` (default) or `fillable` |
| `otsl` | Table structure |
| `formula` | Mathematical expression |
| `code` | Code block |
| `picture` | Image or graphic element; might have a binary data child (`base64` or `uri`) |

### Formatting Elements

Formatting elements represent formatting information within the content of a semantic element and are meant to be interpreted as inline elements. Formatting elements can be nested, e.g. `<bold><italic>bold italic</italic></bold>`.

| Token | Description |
|-------|-------------|
| `bold` | Bold text |
| `italic` | Italic text |
| `underline` | Underlined text |
| `strikethrough` | Strike-through text |
| `superscript` | Superscript |
| `subscript` | Subscript |
| `handwriting` | Handwritten text |
| `rtl` | Right-to-left text direction |
| `hyperlink` | Hyperlink with URI and optional formatted text content |
| `inline class="formula\|code\|picture"` | Inline content: formula, code, or picture. If `class="picture"`, may include one of `base64` or `uri` as a child. |
| `br`| Line break (empty-element tag) |

### Grouping Elements

These elements organize semantic content into logical structures. Groups can not have any location tokens and are intended to create the semantic tree.

| Element | Description | Allowed Children |
|-------|-------------|------------------|
| `<list class="ordered\|unordered">` | List | Any, with every new list item being introduced by a `list_text` element |
| `<group>` | Generic group enabling e.g. association of caption or footnote with the respective document components | |
| `<floating_group class="table\|picture\|code">` | Floating container that groups a floating component with its associated caption, footnotes, and metadata. No `location` tokens. | table, picture, code (as appropriate) |

Lists

- Can in principle contain any children, with every new list item being introduced by a `list_text` element, which also contains any marker and checkbox information.

**footnote regarding docling-core**: What we currently have as instantiations of `FloatingItem` (e.g., TableItem) should have been groups, as the `FloatingItem` contains captions, the `data structure` (e.g., the `data` in TableItem or the `graph` in FormItem) and the footnotes. As a matter of fact, it is currently even more mis-constructed, since the `ProvenanceItem` of the `TableItem` will in fact point to location of only the table, while the captions and footnotes will have their own `ProvenanceItem`.

### Optimized Table Structure Language (OTSL)

Tabular structure and header semantics in DocLang represented by optimized table-structure language (OTSL) tokens.

Each new cell OTSL token (`<fcel/>` with its semantic variants) is interleaved by the sequence of appropriate table cell content tokens (texts, lists, etc.).
OTSL representation has minimized vocabulary and specific rules.
The benefits of describing tables with OTSL in reducing number of structural tokens (5 essential in OTSL vs 28+ in HTML) and shorten structural sequence length to half of HTML representation on average.

Structural tokens define the structure of a table: columns, rows, cells, merged cells. Each cell can then be specified with a semantic variant token if it is a column header, row header, section row separator, or corner header.
Semantic variants of `<fcel/>` token are following the same rules as `<fcel/>` token, and used just to distinguish a function of a table cell: type of header or separator.

| Token | Semantic variant | Description |
|-------|---------|-------------|
| `<otsl>` | - | start of table data structure |
| `<fcel/>`| `<fcel/>` | a new cell with content |
|          | `<ecel/>` | a new cell without content |
|          | `<ched/>`| a new column header cell |
|          | `<rhed/>`| a new row header cell |
|          | `<corn/>`| a new corner header cell |
|          | `<srow/>`| a new section row cell |
| `<lcel/>`| - | left-looking cell, merging with the left neighbor cell to create a horizontal span |
| `<ucel/>`| - | up-looking cell, merging structure with the upper neighbor cell to create a vertical span |
| `<xcel/>`| - | cross cell to merge with both left and upper neighbor cells, for 2D spans |
| `<nl/>`| - | new line, table row separator |

OTSL enables easy error detection and correction during sequence generation, making it LLM friendly.
A notable trait of OTSL is that it has the capability of achieving lossless conversion to HTML.

The OTSL representation follows these syntax rules:

- Left-looking cell rule: The left neighbour of an `<lcel/>` must be either another `<lcel/>` or one of the variants of `<fcel/>`.
- Up-looking cell rule: The upper neighbour of a `<ucel/>` must be either another `<ucel/>` or one of the variants of `<fcel/>`.
- Cross cell rule: The left neighbour of an `<xcel/>` cell must be either another `<xcel/>` or a `<ucel/>`, and the upper neighbour of an `<xcel/>` must be either another `<xcel/>` or an `<lcel/>`.
- First row rule: Only `<lcel/>` and `<fcel/>`(with variants) are allowed in the first row.
- First column rule: Only `<ucel/>` cells and `<fcel/>`(with variants) are allowed in the first column.
- Rectangular rule: The table representation of structural OTSL tokens is always rectangular - all rows must have an equal number of OTSL tokens, terminated with `<nl/>` token.

Example:

```xml
<otsl>
  <ecel/>          <lcel/>                <ched/>Observer 1<lcel/>         <lcel/><nl/>
  <ucel/>          <xcel/>                <ched/>benign    <ched/>malignant<ched/>Total observer 2<nl/>
  <rhed/>Observer 2<rhed/>Benign          <fcel/>13        <fcel/>2        <fcel/>15<nl/>
  <ucel/>          <rhed/>malignant       <fcel/>0         <fcel/>62       <fcel/>62<nl/>
  <ucel/>          <rhed/>Total observer 1<fcel/>13        <fcel/>64       <fcel/>77<nl/>
</otsl>
```

### Pictures of Charts

`<picture>` can include `<class>` with picture classification value. In cases of numerical charts, it is also possible to include `<otsl>` that contain numerical data of a chart. This is applicable for charts with data series that can be represented in a tabular fashion: `bar_chart`, `line_chart`, `pie_chart`, `area_chart`, `scatter_plot`, `bubble_chart`, etc:

```xml
<picture>
  <location value="50"/><location value="50"/>
  <location value="150"/><location value="150"/>
  <uri>assets/bar_chart.png</uri>
  <class>bar_chart</class>
  <otsl>
    <ched/>sales<ched/>2022<ched/>2023<ched/>2024<ched/>2025<nl/>
    <rhed/>ABCDE<fcel/>100M<fcel/>120M<fcel/>110M<fcel/>105M<nl/>
    <rhed/>FGHIJ<fcel/>125M<fcel/>150M<fcel/>175M<fcel/>200M<nl/>
    <rhed/>KLMNO<fcel/>300M<fcel/>270M<fcel/>250M<fcel/>210M<nl/>
  </otsl>
</picture>
```

### Content Tokens

| Token | Description |
|-------|-------------|
| `<marker>`| Marker (eg in `list_item`, within `field_item`, etc) |
| `<checkbox>`| Self-closing elemnt for checkbox status; optional `selected` in {`true`,`false`} defaults to `false`. |
| `<facets>`| Container meant for application-specific properties for derived information, such as summary, classification label, etc. |

The present standard does not prescribe the specific `facets` content, but a possible instantiation could be:

```xml
<doclang>
  <picture>
    <facets>
      <summary>This image shows the distribution of the various data points in the dataset</summary>
      <class>pie_chart</class>
    </facets>
    <location value="50"/><location value="60"/><location value="450"/><location value="360"/>
    <base64>iVBORw0KGgoAAAANSUhEUgAA...truncated...5ErkJggg==</base64>
  </picture>
</doclang>
```

### Metadata Elements

Metadata elements are meant to capture information that is not directly part of the document *content*, but rather:

- deriveable from the document
  - either directly, e.g. a summary of a certain component
  - or in combination with other context, e.g. from external knowledge sources
- or reflects properties of the upstream pipeline, e.g. the VLM that generated the document.

As applications can have varying requirements, this standard defines a set of reserved metadata elements for common use
cases, but also allows for custom metadata elements to be added.
To avoid collisions, custom metadata SHOULD always be properly namespaced, as illustrated in the examples further below.

Document-level metadata is contained in the `<head>` element, while component-level metadata is contained in an `<meta>`
element within the respective component element. We discuss the details in the subsections below.

#### The `head` Element

After the optional `version` element, the `doclang` element can continue with an optional `<head>` element.
Below we list the reserved core metadata elements to be used within `<head>`:

- `title`
- each `author` element can optionally begin with one or more `affiliation` elements
- `date`
- `default_resolution`, containing attributes for the document-level default `width` and `heigth` resolution in pixels; if element is missing, 512x512 is considered the default resolution.
- `page_size`, the actual page size. An element without the `page_no` attribute defines the default size for all pages, when `page_no` is specified it is counted from 1.
- `language`, Identifies the (human) language of the document, e.g., English, German, French, Spanish, Japanese. The content MUST be an [ISO 639-3](https://iso639-3.sil.org/about) language identifier. Optional attributes: `classifier` (the tool/method used, e.g., fastText) and `score` (confidence in [0, 1]). Multiple `language` entries MAY be provided.
- `generated_by`, upstream pipeline information, e.g. VLM ID
- `topic`, topic that the document is most likely to fall in such as Science and Technology, Legal, etc. The topics should preferrably come from some taxonomy. Classifier defines the classifier used for classifying into the given topic and score is the confidence score of classifier and 0<=Scores<=1. This can be one or more.
- `summary`, a summary of the document
- `document_hash`, Hash of the document, whereas hash_function defines the algorithm used to compute the hash, e.g., SHA2. This can be one or more.

Here is an example:

```xml
<doclang>
  <head>
    <!-- reserved elements -->
    <title>My Company's Annual Report</title>
    <author_info>
      <author>Author 1 Name</author>
      <author>
        <affiliation>Affiliation A</affiliation>
        <affiliation>Affiliation B</affiliation>
        Author 2 Name
      </author>
    </author_info>
    <date>2024-01-01</date>
    <language classifier="fastText" score="0.7">eng</language>
    <language classifier="fastText" score="0.2">spa</language>
    <topic topic_taxonomy="taxonomy" score="0.5">Technology</topic>
    <topic topic_taxonomy="taxonomy" score="0.5">Math</topic>
    <document_hash hash_function="sha256sum"/>75f2db0c6124527bf6dd48440f95fc864a5108d28517633f937923a7d8199185</document_hash>
    <summary>This is a summary of the document</summary>
    <generated_by>example_vlm_org/example_vlm_name</generated_by>
    <default_resolution width="512" height="512"/>
    <page_size width="612" height="792"/>
    <page_size page_no="4" width="792" height="612"/>

      <!-- examples of custom elements -->
    <my_company_hap_filter_hate/>0.1</my_company_hap_filter_hate>
    <my_company_hap_filter_abuse/>0.1</my_company_hap_filter_abuse>
    <my_company_hap_filter_profanity/>0.1</my_company_hap_filter_profanity>
  </head>
  <!-- document content -->
</doclang>
```
##### Governance and compliance metadata

In addition to the core metadata elements, publishers can optionally provide metadata pertaining to governance and compliance.
These elements allow the communication of acceptable use, policy, licensing, contact information and compliance requirements.

Governance and compliance metadata MUST be expressed at the document level inside `<head>`.
Component-level governance (e.g., component-specific redaction or extraction restrictions) MAY be expressed inside a component’s `<meta>` when appropriate.

###### Standards reference and interpretation

The standards referenced throughout this Governance and Compliance section are provided to support alignment, interpretation, and interoperability.
They are **informative**, not normative, unless explicitly stated otherwise.

These references are intended to:
- Clarify regulatory or industry concepts reflected by the metadata elements
- Assist implementers in mapping DocLang governance signals to existing compliance programs
- Avoid re-defining legal or regulatory obligations within this standard

DocLang governance metadata does **not** claim conformance to any listed framework by itself.
Rather, it provides structured, machine-readable signals that downstream systems MAY use to support compliance, risk management, and audit workflows.

The following standards and regulations are commonly referenced:

| Standard / Regulation | Scope and relevance |
|---|---|
| **GDPR (EU General Data Protection Regulation)** | Governs processing of personal data, including lawful basis, purpose limitation, data minimization, retention, data subject rights, and cross-border transfer obligations. |
| **EU AI Act** | Establishes obligations related to AI system risk categories, data governance, transparency, and human oversight for AI systems placed on or used within the EU. |
| **ISO/IEC 27001** | International standard for information security management systems (ISMS), covering access control, asset management, logging, and security controls. |
| **ISO/IEC 27701** | Extension to ISO/IEC 27001 focused on privacy information management (PIMS), including controller/processor roles and personal data handling. |
| **ISO/IEC 23894** | Guidance on AI risk management, including lifecycle governance, human oversight, and accountability for AI systems. |
| **HIPAA** | U.S. regulation governing protected health information (PHI), including privacy, security, and breach notification requirements. |
| **PCI DSS** | Security standard for handling payment card data, including storage, processing, and transmission controls. |
| **FedRAMP** | U.S. government program defining security requirements for cloud services used by federal agencies. |

Where multiple standards are referenced for a single metadata element, the intent is to indicate conceptual alignment rather than impose cumulative obligations.
Implementers SHOULD consult authoritative sources and legal counsel to determine applicability within their specific legal and regulatory context.

###### Governance narrative and flow

Governance metadata is intended to travel with the document and provide downstream systems with machine-readable constraints.
The diagram below illustrates how the four governance areas map to common document-to-AI workflows.

```mermaid
flowchart LR
  D["Document content<br/>(DocLang body)"] --> H["<head><br/>Governance metadata"]

  H --> PII["Privacy & PII controls<br/>(pii_*)"]
  H --> EXT["Extraction controls<br/>(extraction_*)"]
  H --> RAG["RAG controls<br/>(rag_*)"]
  H --> TRN["Training controls<br/>(training_*)"]

  D --> X["Extraction pipeline"]
  EXT --> X
  PII --> X
  X --> XD["Extracted dataset / fields"]

  D --> I["Index/Embed pipeline"]
  RAG --> I
  PII --> I
  I --> E["Embeddings / index"]

  E --> Q["Retrieve"]
  RAG --> Q
  Q --> M["Model inference"]
  M --> O["Output"]
  RAG --> O
  PII --> O

  D --> T["Training / fine-tuning pipeline"]
  TRN --> T
  PII --> T
  T --> TD["Training dataset"]
  T --> TM["Trained model"]
```

###### Naming and terminology conventions

This section uses the following terminology consistently:

- **RAG** refers to retrieval-augmented generation workflows that embed/index content and retrieve it at inference time.
- **Extraction** refers to producing structured outputs (fields/records) derived from document content.
- **Training** refers to using content for model training, fine-tuning, evaluation, or benchmarking.
- **Artifacts** refers to derived outputs created by processing the document (e.g., extracted datasets, embeddings/indexes, caches, training datasets).

Where an element carries an enumerated value (e.g., `pii_status`, `rag_embedding_scope`), implementations SHOULD use a controlled vocabulary.
Where an element carries a boolean, implementations SHOULD use explicit `true` / `false` values.

###### Governance overview

Governance metadata is intended to be machine-actionable: it should enable downstream systems (including AI systems) to determine what is permitted, under what constraints, and with what obligations.

###### Licensing and rights

- `licenses` Indicate one or more licenses covering use of the document.

###### Data classification and privacy posture

- `data_classification` One or more data classifications can be given for the document content.
  In general, data classification is not globally standardized. Organizations usually define a classification system suitable for their respective mission.
  These elements allow an organization to classify document sensitivity in their own terms.

###### Acceptable use and purpose limitation

- `acceptable_use` Organizations may express acceptable use cases for the provided document data.

###### Stewardship and contact

- `stewardship` Provides the name of a person and/or organization with governance responsibility at the document owning organization.

###### Access control policy

- `access_policy` Provides the ability to express access policy as well as enumerate roles allowed to access the data.
  Similar to data classification, there are no standards specifying role semantics.
  This element allows organizations to describe access policy and roles in their own terms.

###### Retention and deletion

- `retention_policy` Allows organizations to state retention objectives for the document data.

###### Compliance frameworks

- `compliance_requirements` States the compliance frameworks (regulatory or industrial) governing the lifecycle and use of the documents.

###### Privacy and PII controls

This subsection defines governance signals related to personal data detection, sensitivity, and permitted handling.
Implementations SHOULD use these elements to drive privacy-aware processing (e.g., redaction, restricted access, minimization).

The following optional elements MAY be provided to describe personal data presence, sensitivity, permitted processing, and privacy-related obligations.
Unless otherwise required by an implementation, these elements are intended to be expressed at the document level inside `<head>`.

| Element | Purpose | Standards alignment (non-exhaustive) |
|---|---|---|
| `pii_status` | Indicates whether the document contains PII. | ISO 27701; ISO 27001 A.5/A.8; GDPR Art. 4(1), 5(1) |
| `pii_sensitivity_level` | Classifies the sensitivity level of detected PII. | ISO 27701; GDPR Art. 9–10 |
| `pii_source_type` | Identifies the origin/source of PII (e.g., provided by user, derived, third-party). | GDPR Art. 13–14 |
| `controller_processor_role` | Defines the organizational role for processing (controller/processor or equivalent). | GDPR Art. 24–28 |
| `pii_processing_purpose` | Specifies the purpose of processing (purpose limitation). | GDPR Art. 5(1)(b), Art. 6 |
| `pii_lawful_basis` | Records lawful basis for processing. | GDPR Art. 6(1) |
| `special_category_condition` | Condition for processing special-category data (if applicable). | GDPR Art. 9(2) |
| `pii_minimisation_status` | Indicates whether minimisation has been applied (data minimisation / privacy by design). | GDPR Art. 5(1)(c), Art. 25 |
| `pii_transformation_level` | Indicates transformation applied to PII (e.g., redacted, masked, pseudonymized). | GDPR Recital 26; GDPR Art. 4(5) |
| `reidentification_risk` | Expresses assessed risk of re-identification where transformations are used. | ISO 27701; GDPR Recital 26 |
| `access_control_level` | Required access tier/controls for handling this document. | ISO 27001 A.9; GDPR Art. 32 |
| `ai_use_restriction` | Indicates allowed AI uses or prohibitions for this document’s content. | GDPR Art. 5(1)(b–c) |
| `cross_border_transfer_status` | Indicates whether cross-border transfers occur/are allowed. | GDPR Art. 44–49 |
| `transfer_mechanism` | Indicates transfer mechanism where applicable (e.g., adequacy, SCCs). | GDPR Art. 45–47 |
| `retention_category` | Indicates retention category for personal data contained in the document. | GDPR Art. 5(1)(e) |
| `dsr_impact_flag` | Signals potential impact on data subject rights (DSR handling implications). | GDPR Art. 12–23 |
| `dpia_required` | Indicates whether a DPIA is required for intended processing. | GDPR Art. 35–36 |
| `children_pii_present` | Flags whether children’s data is present. | GDPR Art. 8 |
| `automated_decisioning_relevance` | Indicates whether automated decision-making/profiling obligations apply. | GDPR Art. 22 |
| `logging_monitoring_enabled` | Indicates whether logging/monitoring is enabled for access and processing (accountability/auditability). | ISO 27001 A.12/A.16; GDPR Art. 5(2) |

Implementations SHOULD define controlled vocabularies (and, where applicable, boolean conventions) for these elements.
If an organization already has established internal taxonomies for classification, purpose, lawful basis, access tiers, or transfer mechanisms, those SHOULD be used consistently.

###### Data extraction controls

This subsection defines governance signals that constrain automated extraction, transformation, and downstream use of extracted fields.
Implementations SHOULD use these elements to ensure purpose limitation and auditability of extraction.

The following optional elements MAY be provided to express constraints and obligations related to automated or manual data extraction from the document.
These elements are intended to guide downstream systems that perform field extraction, transformation, enrichment, or export.
Unless otherwise required by an implementation, these elements SHOULD be expressed at the document level inside `<head>`, and MAY be overridden at component level using `<meta>` where finer-grained control is required.

| Element | Purpose | Standards alignment (non-exhaustive) |
|---|---|---|
| `extraction_permitted` | Indicates whether automated data extraction is permitted at all. | GDPR Art. 5(1)(a,b); ISO 27701 |
| `extraction_scope` | Defines which parts or components of the document may be extracted (e.g., full document, tables only, specific sections). | GDPR Art. 5(1)(b,c) |
| `extraction_purpose` | Specifies the allowed purpose(s) for extracted data. | GDPR Art. 5(1)(b); ISO 27701 |
| `extraction_granularity` | Indicates permitted level of granularity (e.g., aggregate only, field-level, record-level). | GDPR Art. 5(1)(c) |
| `pii_extraction_allowed` | Indicates whether PII may be included in extracted outputs. | GDPR Art. 6; ISO 27701 |
| `sensitive_data_extraction_allowed` | Indicates whether special-category or sensitive data may be extracted. | GDPR Art. 9–10 |
| `extraction_transformation_required` | Specifies required transformations during extraction (e.g., redaction, masking, pseudonymization). | GDPR Art. 25; Recital 26 |
| `extraction_output_constraints` | Constrains allowed output formats or destinations for extracted data. | ISO 27001 A.8; GDPR Art. 32 |
| `downstream_sharing_permitted` | Indicates whether extracted data may be shared with downstream systems or third parties. | GDPR Art. 5(1)(a,b); Art. 28 |
| `downstream_usage_restrictions` | Specifies restrictions on how extracted data may be used downstream. | GDPR Art. 5(1)(b) |
| `extraction_audit_required` | Indicates whether extraction activities must be logged and auditable. | GDPR Art. 5(2); ISO 27001 A.12 |
| `extraction_audit_retention` | Specifies retention period for extraction audit logs. | GDPR Art. 5(1)(e) |
| `human_in_the_loop_required` | Indicates whether human review/approval is required before or after extraction. | ISO 23894; ISO 27701 |
| `automated_decisioning_dependency` | Indicates whether extracted data feeds automated decision-making systems. | GDPR Art. 22 |

Implementations SHOULD define controlled vocabularies for scope, purpose, granularity, transformations, and output constraints.
Where extraction interacts with PII, these elements SHOULD be interpreted in conjunction with the Privacy and PII controls defined above.

###### RAG and retrieval controls

This subsection defines governance signals that constrain whether and how document content may be embedded, indexed, chunked, retrieved, and presented to models during retrieval-augmented generation.
Implementations SHOULD use these elements to control exposure, leakage risk, and attribution requirements.

The following optional elements MAY be provided to govern whether and how document content may be embedded, indexed, retrieved, and surfaced to models or users as part of retrieval-augmented generation (RAG) workflows.
These elements are intended to control exposure risk, attribution, and downstream use of retrieved content.
Unless otherwise required by an implementation, these elements SHOULD be expressed at the document level inside `<head>`, and MAY be overridden at component level using `<meta>` where finer-grained control is required.

| Element | Purpose | Standards alignment (non-exhaustive) |
|---|---|---|
| `rag_permitted` | Indicates whether the document may be used in RAG workflows at all. | GDPR Art. 5(1)(a,b); ISO 27701 |
| `rag_indexing_allowed` | Indicates whether the document content may be indexed or embedded for retrieval. | GDPR Art. 5(1)(b,c); ISO 27001 A.8 |
| `rag_embedding_scope` | Defines which parts or components of the document may be embedded (e.g., full document, summaries only, specific sections). | GDPR Art. 5(1)(b,c) |
| `rag_chunking_constraints` | Specifies constraints on chunking strategy (e.g., max size, boundaries, semantic-only). | ISO 23894; privacy-by-design principles |
| `rag_query_restrictions` | Defines restrictions on the types of queries that may retrieve this content. | GDPR Art. 5(1)(b) |
| `rag_output_attribution_required` | Indicates whether attribution or citation is required when content is retrieved or surfaced. | ISO 27001 A.18; copyright best practice |
| `rag_output_transformation_required` | Specifies required transformations on retrieved content (e.g., summarization, redaction). | GDPR Art. 25; Recital 26 |
| `rag_pii_exposure_allowed` | Indicates whether retrieved content may expose PII. | GDPR Art. 6; Art. 32 |
| `rag_sensitive_data_exposure_allowed` | Indicates whether special-category or sensitive data may be exposed via retrieval. | GDPR Art. 9–10 |
| `rag_downstream_sharing_permitted` | Indicates whether retrieved content may be shared beyond the immediate RAG response. | GDPR Art. 5(1)(a,b); Art. 28 |
| `rag_caching_allowed` | Indicates whether retrieved content may be cached for performance or reuse. | ISO 27001 A.8; GDPR Art. 5(1)(e) |
| `rag_cache_retention` | Specifies retention period for cached embeddings or retrieved content. | GDPR Art. 5(1)(e) |
| `rag_audit_required` | Indicates whether retrieval events must be logged and auditable. | GDPR Art. 5(2); ISO 27001 A.12 |
| `rag_audit_retention` | Specifies retention period for RAG access and retrieval logs. | GDPR Art. 5(1)(e) |
| `rag_model_scope` | Restricts which models or model classes may access this content via RAG. | ISO 23894; internal governance |

Implementations SHOULD define controlled vocabularies for embedding scope, chunking constraints, query restrictions, and model scope.
Where RAG interacts with PII or sensitive data, these elements SHOULD be interpreted in conjunction with the Privacy and PII controls defined above.

###### Document training controls

This subsection defines governance signals that constrain whether and how document content may be used for training, fine-tuning, or evaluation of models.
Implementations SHOULD use these elements to ensure licensing compliance, privacy protection, provenance tracking, and alignment with regulatory and contractual obligations.

The following optional elements MAY be provided to govern whether and how document content may be used for model training, fine-tuning, evaluation, or benchmarking.
These elements are intended to ensure licensing compliance, privacy protection, provenance tracking, and alignment with regulatory and contractual obligations.
Unless otherwise required by an implementation, these elements SHOULD be expressed at the document level inside `<head>`, and MAY be overridden at component level using `<meta>` where finer-grained control is required.

| Element | Purpose | Standards alignment (non-exhaustive) |
|---|---|---|
| `training_permitted` | Indicates whether the document may be used for any form of model training or fine-tuning. | GDPR Art. 5(1)(a,b); ISO 27701 |
| `training_scope` | Defines which parts or components of the document may be used for training (e.g., full document, summaries only, specific sections). | GDPR Art. 5(1)(b,c) |
| `training_purpose` | Specifies the intended purpose of training (e.g., general models, domain-specific models, evaluation only). | GDPR Art. 5(1)(b) |
| `training_model_type` | Restricts the types or classes of models that may be trained using this content. | ISO 23894; internal governance |
| `training_data_retention` | Specifies retention period for training datasets derived from this document. | GDPR Art. 5(1)(e) |
| `training_dataset_reuse_allowed` | Indicates whether derived training datasets may be reused beyond the initial training purpose. | GDPR Art. 5(1)(b) |
| `training_derivative_sharing_permitted` | Indicates whether trained models or derivatives may be shared with third parties. | GDPR Art. 28; licensing obligations |
| `training_pii_included` | Indicates whether training data may include PII. | GDPR Art. 6; ISO 27701 |
| `training_sensitive_data_included` | Indicates whether special-category or sensitive data may be included in training. | GDPR Art. 9–10 |
| `training_transformation_required` | Specifies required transformations prior to training (e.g., anonymization, pseudonymization). | GDPR Art. 25; Recital 26 |
| `training_provenance_required` | Indicates whether provenance metadata must be retained for training records. | ISO 27001 A.12; AI accountability best practice |
| `training_audit_required` | Indicates whether training usage must be logged and auditable. | GDPR Art. 5(2); ISO 27001 A.12 |
| `training_audit_retention` | Specifies retention period for training-related audit logs. | GDPR Art. 5(1)(e) |
| `model_output_usage_constraints` | Specifies constraints on use of models trained on this content (e.g., internal-only, non-commercial). | Licensing and IP best practice |
| `right_to_be_forgotten_applicability` | Indicates whether erasure obligations apply to trained models or datasets. | GDPR Art. 17; emerging AI guidance |

Implementations SHOULD define controlled vocabularies for training scope, purpose, model type, and transformation requirements.
Where training involves personal or sensitive data, these elements SHOULD be interpreted in conjunction with the Privacy and PII controls defined above.

###### Minimal and full governance profiles

Implementations may adopt either a minimal governance profile (recommended baseline) or a full governance profile (richer control surface).
These profiles are informative and provided to encourage consistent adoption.

**Minimal profile (recommended baseline)**

| Area | Recommended elements |
|---|---|
| Licensing & compliance | `licenses`, `compliance_requirements` |
| Classification & access | `data_classification`, `access_policy` (or `access_control_level` where used), `retention_policy` |
| PII | `pii_status`, `pii_sensitivity_level` (when `pii_status` is `present`) |
| Extraction | `extraction_permitted`, `pii_extraction_allowed` |
| RAG | `rag_permitted`, `rag_indexing_allowed`, `rag_pii_exposure_allowed` |
| Training | `training_permitted`, `training_pii_included` |

**Full profile (expanded control surface)**

The full profile includes the minimal profile plus additional elements from the PII, Extraction, RAG, and Training subsections to express:
- purpose limitation and lawful basis
- component-level scope constraints
- transformation requirements (redaction/masking/pseudonymization)
- caching/index retention and auditability
- model scope restrictions and provenance requirements

Producers SHOULD avoid emitting elements with ambiguous free-text values when a controlled vocabulary is available.

###### Example

Example use of the governance and compliance elements is shown below:

```xml
<doclang>
  <head>
    <!-- reserved elements -->
    <title>My Company's Annual Report</title>
    <author_info>
      <author>Author 1 Name</author>
    </author_info>
    <date>2024-01-01</date>
    <language classifier="fastText" score="0.7">eng</language>
    <topic topic_taxonomy="taxonomy" score="0.5">Technology</topic>
    <document_hash hash_function="sha256sum"/>75f2db0c6124527bf6dd48440f95fc864a5108d28517633f937923a7d8199185</document_hash>
    <summary>This is a summary of the document</summary>
    <generated_by>example_vlm_org/example_vlm_name</generated_by>

    <licenses>
      <license>https://www.apache.org/licenses/LICENSE-2.0</license>
    </licenses>

    <data_classification>
      <data_class>confidential</data_class>
      <data_class>personal information</data_class>
    </data_classification>

    <acceptable_use>
      <purpose>General-purpose language models</purpose>
      <purpose>Sales and marketing</purpose>
    </acceptable_use>

    <stewardship>
      <steward>
        <name>Charles Owens</name>
        <contact>abc@some.org</contact>
        <org>Dataset Organization</org>
      </steward>
    </stewardship>

    <access_policy>
      <policy>
        <ref>http://www.some.org/policies/AC-2345</ref>
        <roles>
          <role>viewer</role>
          <role>reader</role>
        </roles>
      </policy>
    </access_policy>

    <retention_policy>
      <policy>
        <ref>http://www.some.org/policies/AC-2345</ref>
        <retention_period unit="year">5</retention_period>
        <deletion_method>permanent secure deletion</deletion_method>
        <documentation>record deletion event, date, method and personnel responsible</documentation>
      </policy>
    </retention_policy>

    <compliance_requirements>
      <compliance_req>GDPR</compliance_req>
      <compliance_req>HIPAA</compliance_req>
      <compliance_req>FedRAMP</compliance_req>
      <compliance_req>PCI DSS</compliance_req>
      <compliance_req>EU AI Act</compliance_req>
    </compliance_requirements>

  </head>
  <!-- document content -->
</doclang>
```

###### Consolidated example (PII + extraction + RAG + training)

The following example illustrates a single `<head>` that combines Privacy and PII controls, Data extraction controls, RAG and retrieval controls, and Document training controls.
Implementations MAY choose to interpret these as organization-wide defaults for the document, and MAY override at component level using `<meta>` for finer-grained control.

```xml
<doclang>
  <head>
    <!-- core metadata (illustrative) -->
    <title>Customer Support Case File</title>
    <date>2025-01-15</date>
    <language classifier="fastText" score="0.92">eng</language>
    <generated_by>example_pipeline/doc_ingest_v2</generated_by>

    <!-- licensing / classification / compliance (existing governance elements) -->
    <licenses>
      <license>https://www.apache.org/licenses/LICENSE-2.0</license>
    </licenses>

    <data_classification>
      <data_class>confidential</data_class>
      <data_class>personal information</data_class>
    </data_classification>

    <acceptable_use>
      <purpose>Customer support automation</purpose>
      <purpose>Internal analytics</purpose>
    </acceptable_use>

    <compliance_requirements>
      <compliance_req>GDPR</compliance_req>
      <compliance_req>ISO/IEC 27001</compliance_req>
      <compliance_req>ISO/IEC 27701</compliance_req>
    </compliance_requirements>

    <!-- Privacy and PII controls -->
    <pii_status>present</pii_status>
    <pii_sensitivity_level>medium</pii_sensitivity_level>
    <pii_source_type>user_provided</pii_source_type>
    <controller_processor_role>controller</controller_processor_role>
    <pii_processing_purpose>case_resolution</pii_processing_purpose>
    <pii_lawful_basis>legitimate_interest</pii_lawful_basis>
    <pii_minimisation_status>applied</pii_minimisation_status>
    <pii_transformation_level>pseudonymized</pii_transformation_level>
    <reidentification_risk>low</reidentification_risk>
    <access_control_level>restricted</access_control_level>
    <ai_use_restriction>no_general_training</ai_use_restriction>
    <cross_border_transfer_status>not_permitted</cross_border_transfer_status>
    <retention_category>support_case_records</retention_category>
    <dsr_impact_flag>true</dsr_impact_flag>
    <dpia_required>false</dpia_required>
    <logging_monitoring_enabled>true</logging_monitoring_enabled>

    <!-- Data extraction controls -->
    <extraction_permitted>true</extraction_permitted>
    <extraction_scope>tables_and_forms_only</extraction_scope>
    <extraction_purpose>case_metrics</extraction_purpose>
    <extraction_granularity>field_level</extraction_granularity>
    <pii_extraction_allowed>false</pii_extraction_allowed>
    <sensitive_data_extraction_allowed>false</sensitive_data_extraction_allowed>
    <extraction_transformation_required>redact</extraction_transformation_required>
    <extraction_output_constraints>internal_systems_only</extraction_output_constraints>
    <downstream_sharing_permitted>false</downstream_sharing_permitted>
    <extraction_audit_required>true</extraction_audit_required>
    <extraction_audit_retention unit="day">90</extraction_audit_retention>
    <human_in_the_loop_required>true</human_in_the_loop_required>

    <!-- RAG and retrieval controls -->
    <rag_permitted>true</rag_permitted>
    <rag_indexing_allowed>true</rag_indexing_allowed>
    <rag_embedding_scope>summaries_only</rag_embedding_scope>
    <rag_chunking_constraints>max_512_tokens</rag_chunking_constraints>
    <rag_query_restrictions>support_intent_only</rag_query_restrictions>
    <rag_output_attribution_required>true</rag_output_attribution_required>
    <rag_output_transformation_required>summarize_and_redact</rag_output_transformation_required>
    <rag_pii_exposure_allowed>false</rag_pii_exposure_allowed>
    <rag_sensitive_data_exposure_allowed>false</rag_sensitive_data_exposure_allowed>
    <rag_downstream_sharing_permitted>false</rag_downstream_sharing_permitted>
    <rag_caching_allowed>true</rag_caching_allowed>
    <rag_cache_retention unit="day">30</rag_cache_retention>
    <rag_audit_required>true</rag_audit_required>
    <rag_audit_retention unit="day">90</rag_audit_retention>
    <rag_model_scope>enterprise_internal_models</rag_model_scope>

    <!-- Document training controls -->
    <training_permitted>false</training_permitted>
    <training_scope>none</training_scope>
    <training_purpose>none</training_purpose>
    <training_model_type>none</training_model_type>
    <training_dataset_reuse_allowed>false</training_dataset_reuse_allowed>
    <training_derivative_sharing_permitted>false</training_derivative_sharing_permitted>
    <training_pii_included>false</training_pii_included>
    <training_sensitive_data_included>false</training_sensitive_data_included>
    <training_provenance_required>true</training_provenance_required>
    <training_audit_required>true</training_audit_required>
    <training_audit_retention unit="day">365</training_audit_retention>
    <model_output_usage_constraints>internal_only</model_output_usage_constraints>
    <right_to_be_forgotten_applicability>true</right_to_be_forgotten_applicability>

  </head>
  <!-- document content -->
</doclang>
```

Notes:

- The example uses illustrative values. Implementations SHOULD define controlled vocabularies for enums such as `pii_status`, `pii_sensitivity_level`, `extraction_scope`, `rag_embedding_scope`, and `training_model_type`.
- When `training_permitted` is `false`, implementations SHOULD treat training-related fields as either omitted or set to explicit "none" values.
- Where retention elements include a `unit` attribute, producers MUST use consistent units and pre-normalized values.

### The `meta` Element

The `meta` element is used to contain metadata about a specific component of the document.

Below we list the reserved metadata elements to be used within `<meta>`:

- `summary`
- `class`
- `language`

Here is an example usage, for instance considering a picture:

```xml
<doclang>
  <picture>
    <meta>
      <summary>This image shows the distribution of the various data points in the dataset</summary>
      <class>pie_chart</class>
    </meta>
    <location value="50"/><location value="60"/><location value="450"/><location value="360"/>
    <base64>iVBORw0KGgoAAAANSUhEUgAA...truncated...5ErkJggg==</base64>
  </picture>
</doclang>
```

### Continuation Tokens

For content spanning page breaks:

| Token | Description |
|-------|-------------|
| `<thread id="N"/>` | Special element for capturing content that spans across pages (see [Split Structure](#split-structure)); `id` is a required identifier reused across parts. |
| `<h_thread id="N"/>` | Special element for horizontal stitching of table content (see [Split Structure](#split-structure)); `id` is a required identifier reused across parts. |

### Binary Data Elements

Binary data elements encode non-text payloads that semantic content can reference or embed. They can appear directly under a page’s flow (page-level) or as children of elements that carry binary payloads.

- `base64`: Embeds binary data as a base64-encoded string between the tags.
- `uri`: Provides a reference to an external or local resource via a valid URI or filesystem path.

Usage rules:

- Allowed parents: `picture`, `inline class="picture"`, and page-level flow (i.e., between `page_break` markers) when associating a resource with the current page.
- For `picture` and `inline class="picture"`, include at most one of `base64` or `uri` as a child.
- Content of `base64` is a raw base64 string (no data URI prefix).
- Content of `uri` must be a valid URI or filesystem path resolvable by the implementation.

Examples:

```xml
<!-- Block image with a URI -->
<picture>
  <location value="100"/><location value="200"/><location value="300"/><location value="400"/>
  <uri>assets/figures/fig1.png</uri>
  <caption>Figure 1: System diagram</caption>
</picture>

<!-- Block image with embedded base64 -->
<picture>
  <location value="50"/><location value="60"/><location value="450"/><location value="360"/>
  <base64>iVBORw0KGgoAAAANSUhEUgAA...truncated...5ErkJggg==</base64>
</picture>

<!-- Inline image referenced by URI inside text -->
<text>
  The logo <inline class="picture"><uri>assets/logo.png</uri></inline> appears here.
</text>

<!-- Page-level binary payload associated with the current page -->
<page_break/>
<uri>assets/page_2_background.png</uri>
<text>Page 2 content...</text>
```

### Vector graphics Elements

If you want to include vector graphics elements, DocLang allow you to include SVG: enclosed in `<svg> ... </svg>`.

## Grammar and Structure Rules

### Simple Document Structure

In the simplest document example, document elements are in a flat list,

```xml
<doclang version="1.0.0">
  <heading level="1">Research Paper Title</heading>
  <heading level="2">Abstract</heading>
  <text>This paper presents...</text>
  <heading level="2">Introduction</heading>
  <text>In recent years...</text>
  <heading level="3">Background</heading>
  <text>Previous work has shown...</text>
</doclang>
```

In case of page-layout information, the coordinates are provided only at the semantic element level. Coordinates are not allowed at the group level.

```xml
<doclang version="1.0.0">
  <heading level="1">
    <location value="10"/><location value="20"/><location value="30"/><location value="40"/>
    Research Paper Title
  </heading>

  <heading level="2">
    <location value="10"/><location value="20"/><location value="30"/><location value="40"/>
    Abstract
  </heading>
  <text>
    <location value="10"/><location value="20"/><location value="30"/><location value="40"/>
    This paper presents...
  </text>

  <heading level="2">Introduction</heading>
  <text>In recent years...</text>

  <heading level="3">Background</heading>
  <text>Previous work has shown...</text>
</doclang>
```

### Code snippets

Code content can appear inline via `inline class="code"` or as block code via `code`. To classify the programming language of a block, include a `<class>...</class>` child inside `code`. When using groups, place coordinates only on semantic elements (e.g., `caption`, `code`), not on the `group` itself.

Basic inline code

```xml
<text>
  Install with <inline class="code">pip install docling</inline> and run.
  For environment checks, use <inline class="code">python --version</inline>.
  Inline code preserves spacing and punctuation.
  <br/>
  Example path: <inline class="code">/usr/local/bin</inline>
  <br/>
  Variables like <inline class="code">API_KEY</inline> should not be committed.
  <br/>
  Use <inline class="code">Ctrl+C</inline> to stop the server.
  <br/>
  Command substitution: <inline class="code">$(echo hello)</inline>
  <br/>
  JSON snippet: <inline class="code">{"ok":true}</inline>
  <br/>
  Escaping: <inline class="code">&lt;tag&gt;value&lt;/tag&gt;</inline>
  <br/>
  Code fragments can mix with <bold>formatting</bold> seamlessly.
  <br/>
  Use backticks sparingly; DocLang uses explicit tokens instead.
  <br/>
  End of examples.

</text>
```

Basic block without language

```xml
<code>
  echo "Hello, world!"
  echo "Logs go to stdout by default"
</code>
```

Block with language classification via `<class>`

```xml
<code>
  <class>python</class>
  def add(a, b):
      return a + b

  if __name__ == "__main__":
      print(add(2, 3))
</code>
```

Grouped code with caption and coordinates

```xml
<group>
  <caption>
    <location value="10"/><location value="20"/><location value="400"/><location value="60"/>
    Listing 1: Minimal HTTP server
  </caption>
  <code>
    <location value="10"/><location value="80"/><location value="400"/><location value="300"/>
    <class>javascript</class>
    // Minimal Node.js server
    import http from 'node:http';
    const server = http.createServer((req, res) => {
      res.end('OK');
    });
    server.listen(3000);
  </code>
  <footnote>Source: examples/code/server.js</footnote>
</group>
```

Block with alternative language classification

```xml
<code>
  <class>C++</class>
  #include <iostream>
  int main(){ std::cout << "hi"; }
</code>
```

Long code blocks can be split across pages using continuation tokens; keep `<class>` in the first fragment.

```xml
<code>
  <class>bash</class>
  # Part 1
  seq 1 5 | while read n; do echo $n; done
  <thread id="code-42"/>
</code>
<page_break/>
<code>
  # Part 2 (continued)
  <thread id="code-42"/>
  echo "done"
</code>
```

### Math and Equations

All math is authored as LaTeX inside `inline class="formula"` (inline) or `formula` (block). Do not use `<class>` for math; language classification is not applicable here. The optional `<marker>` child inside `formula` carries the printed equation number or label (e.g., “(1)”, “Eq. 3”). If present, include it as plain text within `<marker>`.

Inline math examples

```xml
<text>
  The famous relation <inline class="formula">E = mc^2</inline> connects mass and energy.
  For small x, <inline class="formula">\sin x \approx x - x^3/3!</inline> holds.
  The binomial: <inline class="formula">(a+b)^n = \sum_{k=0}^n \binom{n}{k} a^{n-k} b^k</inline>.
</text>
```

Basic block formula (no numbering)

```xml
<formula>
  \int_{-\infty}^{\infty} e^{-x^2}\,dx = \sqrt{\pi}
</formula>
```

Block formula with optional marker (numbering/label)

```xml
<formula>
  <marker>(1)</marker>
  a^2 + b^2 = c^2
</formula>
```

Grouped formula with caption and coordinates

```xml
<group>
  <caption>
    <location value="10"/><location value="20"/><location value="400"/><location value="60"/>
    Equation for the normal distribution
  </caption>
  <formula>
    <location value="10"/><location value="80"/><location value="400"/><location value="150"/>
    <marker>(2)</marker>
    f(x) = \frac{1}{\sigma\sqrt{2\pi}}\,\exp\!\left(-\frac{(x-\mu)^2}{2\sigma^2}\right)
  </formula>
  <footnote>Parameters: mean \mu and standard deviation \sigma.</footnote>
  <!-- Note: Coordinates apply to semantic elements like caption/formula, not the group. -->

</group>
```

Multi-line LaTeX (align) in a single formula

```xml
<formula>
  <marker>Eq. 3</marker>
  \begin{align}
    \nabla\cdot\mathbf{E} &= \frac{\rho}{\varepsilon_0} \\
    \nabla\cdot\mathbf{B} &= 0
  \end{align}
</formula>
```

Cross-page block formula with continuation

```xml
<formula>
  <marker>(4)</marker>
  \begin{equation}
    \mathbf{F}(t) = \int_0^t e^{A(t-\tau)}\,\mathbf{b}(\tau)\,d\tau
  \end{equation}
  <thread id="eq-100"/>
</formula>
<page_break/>
<formula>
  <thread id="eq-100"/>
  % Optional tail content if the printed equation spans pages
</formula>
```

Notes

- All math content is LaTeX; omit `$...$` or `\[...\]` delimiters since the tag conveys math context.
- `<marker>` is optional. Include it only when the page shows an equation number/label.
- Place coordinates on `formula` and `caption` as needed; never on the surrounding `group`.

### Tables

DocLang separates the table’s structure from its surrounding semantics:

- `group`: Semantic container that may include `caption`, multiple `footnote` elements, and exactly one `otsl` child for the structure. Do not put coordinates on the `group`.
- `otsl`: The structural table token sequence. Put the table region’s coordinates on `otsl` for each page fragment. Cells are created by structural tokens (e.g., `<fcel/>`, `<ched/>`) and their content follows immediately after each cell token.

Basic example

```xml
<group>
  <caption>
    <location value="40"/><location value="80"/><location value="540"/><location value="110"/>
    Table 1: Experimental Results
  </caption>
  <otsl>
    <location value="40"/><location value="130"/><location value="540"/><location value="320"/>
    <ched/>Method<ched/>Accuracy<nl/>
    <fcel/>Baseline<fcel/>0.85<nl/>
    <fcel/>Proposed<fcel/>0.92<nl/>
  </otsl>
  <footnote>Accuracy reported on validation set.</footnote>

</group>
```

Peculiarities and continuation

1) Broken over rows (vertical split across pages)

Use `<continue_row id="..."/>` at the end of the first fragment and the start of the next fragment’s `otsl`.

```xml
<group>
  <caption>Table 2: Long Results</caption>
  <otsl>
    <location value="40"/><location value="120"/><location value="540"/><location value="760"/>
    <ched/>ID<ched/>Name<ched/>Score<nl/>
    <fcel/>1<fcel/>Alice<fcel/>91<nl/>
    <fcel/>2<fcel/>Bob<fcel/>88<nl/>
    <continue_row id="T-rows"/>
  </otsl>
</group>
<page_break/>
<group>
  <otsl>
    <location value="40"/><location value="80"/><location value="540"/><location value="300"/>
    <continue_row id="T-rows"/>
    <fcel/>3<fcel/>Cara<fcel/>95<nl/>
    <fcel/>4<fcel/>Dan<fcel/>89<nl/>
  </otsl>
</group>
```

2) Broken over columns (horizontal split across facing pages)

Use `<continue_col id="..."/>` to indicate that columns continue on an adjacent page. Place it at the right edge of the left fragment and the left edge of the right fragment.

```xml
<!-- Left page -->
<group>
  <otsl>
    <location value="40"/><location value="120"/><location value="300"/><location value="760"/>
    <ched/>Metric<ched/>Model A<nl/>
    <fcel/>Accuracy<fcel/>0.92<nl/>
    <fcel/>F1<fcel/>0.90<nl/>
    <continue_col id="T-cols"/>
  </otsl>
</group>

<!-- Right page -->
<group>
  <otsl>
    <location value="320"/><location value="120"/><location value="820"/><location value="760"/>
    <continue_col id="T-cols"/>
    <ched/>Model B<nl/>
    <fcel/>0.93<nl/>
    <fcel/>0.91<nl/>
  </otsl>
</group>
```

3) Rich cells (cells can contain arbitrary document content)

Immediately after a cell-creating token (e.g., `<fcel/>`, `<ched/>`), place the cell’s content, which may include `text`, `list`, even nested `group` elements like another `table` or `picture`.

```xml
<group>
  <caption>Table 3: Rich Cells</caption>
  <otsl>
    <location value="40"/><location value="200"/><location value="560"/><location value="620"/>
    <ched/>Description<ched/>Details<nl/>
    <fcel/>
      <text>Pipeline steps</text>
    <fcel/>
      <list class="unordered">
        <list_text><marker>•</marker>Ingest</list_text>
        <list_text><marker>•</marker>Process</list_text>
        <list_text><marker>•</marker>Export</list_text>
      </list>
    <nl/>
    <fcel/>
      <text>Nested table</text>
    <fcel/>
      <group>
        <caption>Inner table</caption>
        <otsl>
          <ched/>Key<ched/>Value<nl/>
          <fcel/>A<fcel/>1<nl/>
          <fcel/>B<fcel/>2<nl/>
        </otsl>
      </group>
    <nl/>
    <fcel/>
      <text>Image</text>
    <fcel/>
      <picture>
        <uri>assets/img/sample.png</uri>
        <caption>Example image inside a cell</caption>
      </picture>
    <nl/>
  </otsl>
</group>
```

Notes

- Coordinates go on `otsl`, `caption`, and other semantic children; never on the `group`.
- Row- and column-wise splits use `continue_row` and `continue_col` respectively; merge fragments by matching `id`s.
- OTSL follows the rectangular rule; ensure each row has the same number of structural tokens up to `<nl/>`.
- Rich cells can include any valid DocLang content; keep content immediately after the corresponding cell token.

### Lists

Lists can in principle contain any children, with every new list item being introduced by a `list_text` element, which also contains any marker and checkbox information.

Unordered list with optional markers

```xml
<list class="unordered">
  <list_text>
    <marker>•</marker>
    First item with <bold>bold</bold> text
  </list_text>
  <list_text>
    <!-- Marker with its own coordinates -->
    <marker>
      <location value="50"/><location value="110"/><location value="60"/><location value="120"/>
      •
    </marker>
    Second item
  </list_text>
</list>
```

Ordered list; markers are optional and can hold the printed numbering

```xml
<list class="ordered">
  <list_text>
    <marker>1.</marker>
    Install dependencies
  </list_text>
  <list_text>
    <marker>2.</marker>
    Run tests
  </list_text>
  <list_text>
    <!-- No marker provided; numbering can be inferred from order -->
    Ship release
  </list_text>
</list>
```

Checkbox items with selection state; markers optional

```xml
<list class="unordered">
  <list_text>
    <checkbox class="selected"/>
    Completed task
  </list_text>
  <list_text>
    <checkbox class="unselected"/>
    Pending task
  </list_text>
</list>
```

Nested lists (mixing ordered and unordered)

```xml
<list class="ordered">
  <list_text>
    <marker>1.</marker>
    Setup project
  </list_text>
  <list class="unordered">
    <list_text>
      <marker>•</marker>
      Create virtual environment
    </list_text>
    <list_text>
      <marker>•</marker>
      Configure linter
    </list_text>
  </list>
  <list_text>
    <marker>2.</marker>
    Implement features
  </list_text>
</list>
```

Page breaks and continuation

Lists can span multiple pages. Use `<thread id="..."/>` to indicate continuation. You may thread the whole list and, if a particular component, e.g. a `text` is broken, also thread the component itself.

List split across pages

```xml
<list class="ordered">
  <thread id="L1"/>
  <list_text><marker>1.</marker>First item</list_text>
  <list_text><marker>2.</marker>Second item</list_text>
</list>
<page_break/>
<list class="ordered">
  <thread id="L1"/>
  <list_text><marker>3.</marker>Third item</list_text>
</list>
```

Single list-item broken by a page break

```xml
<list class="unordered">
  <thread id="L2"/>
  <list_text>
    <thread id="I7"/>
    <marker>•</marker>
    This item starts on page 1 and continues
  </list_text>
</list>
<page_break/>
<list class="unordered">
  <thread id="L2"/>
  <list_text>
    <thread id="I7"/>
    on page 2 until it ends.
  </list_text>
</list>
```

Notes

- `<marker>` is optional. Include it when the printed glyph/number is visible.
- `<marker>` can include its own `location` coordinates to pinpoint bullet/number placement.
- Lists can nest as shown above.
- When broken across pages, close items before the `page_break`, then re-open and continue with matching `thread` ids after the break.

### Fields

Fields provide a flexible structure for representing key-value data and structured content. The field elements allow for more flexible document structures where keys and values may be separated by other content or organized in complex layouts.

| Token | Description |
|-------|-------------|
| `<field_region>` | Field region container; contains at least one `field_item` as descendant |
| `<field_item>` | Field item container; may contain 0-1 `key` and 0-many `value` elements as descendants |
| `<field_heading>` | Field heading within a field region; has an optional attribute `level` |
| `<key>` | Key of the field item: can be a descendant of `field_item` |
| `<value>` | Value of the field item: can be a descendant of `field_item`; optional `class` attribute with values `read_only` (default) or `fillable` |
| `<hint>` | Hint for a fillable value field; recommended to be used within the context of a `field_item`; can describe a format, example, or additional description |

#### Field Structure Rules

- A `field_region` must contain at least one `field_item` as a descendant (not necessarily a direct child)
- A `field_item` may contain 0 or 1 `key` element as a descendant
- A `field_item` may contain 0 or more `value` elements as descendants
- Values within a `field_item` are implicitly associated with the `key` in that item
- A `field_heading` should have a `field_region` as an ancestor
- Field elements can contain any other DocLang elements (text, pictures, lists, etc.)
- The `value` element has an optional `class` attribute:
  - `class="read_only"` (default): Indicates a pre-filled, non-editable value
  - `class="fillable"`: Indicates an empty or editable field that can be filled in
- The `hint` element is recommended to be used within a `field_item` context to provide guidance for fillable values
- `<key>` or `<value>` are not necessarily just textual and can contain pictures, multiline text, etc.

#### Field region examples

<details>
  <summary>Simple key-values</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_00.png)

  ```xml
  <field_region>
      <field_item>
          <key>Firma:</key>
          <value>Holcim ... GmbH</value>
      </field_item>
      <field_item>
          <key>Datum:</key>
        <value>23.08.2019</value>
      </field_item>
      ...
      <field_item>
          <key>Petrograph. Typ:</key>
          <value>Quartiarer Sand + Kies</value>
      </field_item>
  </field_region>
  ```

</details>

<details>
  <summary>Nesting forms and using form headings</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_01.png)

  ```xml
  <field_region>
    <field_heading>
        <marker>14.</marker>
        Transport Information
    </field_heading>
    <field_region>
        <field_heading>
            Land transport ... (Germany)
        </field_heading>
        <field_item>
            <key>GGVS/GGVE class:</key>
            <value>8</value>
        </field_item>
        <field_item>
            <key>ADR/RID class:</key>
            <value>8</value>
        </field_item>
        ...
    </field_region>
    <field_item>
        <key>River transport ADN/ADNR</key>
        <value>not examined</value>
    </field_item>
    <field_region>
        <field_heading>
            Sea transport IMDG
        </field_heading>
        ...
    </field_region>
    ...
    <text>
        The transport ... considered.
    </text>
    <text>
        THESE TRANSPORT ... PACK!
    </text>
  </field_region>
  ```

</details>

<details>
  <summary>Fillable form</summary>

  <!-- blank line after <summary> is important -->

  <table><tr><td>

  ```xml
  <field_region>
      <field_item>
          <key>Description</key>
          <value>A.A. Cat</value>
      </field_item>
      <field_item>
          <key>Quant.</key>
          <value></value>
      </field_item>
      <field_item>
          <key>Un</key>
          <value></value>
      </field_item>
      <field_item>
          <key>Measure</key>
          <value></value>
      </field_item>
      <field_item>
          <key>Price (in currency)</key>
          <value></value>
      </field_item>
      <field_item>
          <key>Un</key>
          <value></value>
      </field_item>
      <field_item>
          <key>Total</key>
          <value></value>
      </field_item>
      <text></text>
      <field_region>
          <field_item>
              <key>Delivery Cost</key>
              <value></value>
          </field_item>
          <field_item>
              <key>Maintenance</key>
              <value></value>
          </field_item>
          ...
      <field_region>
      <field_region>
          <field_item>
              <key>Date and time of delivery:</key>
              <value></value>
          </field_item>
          ...
          <field_item>
              <key>Guarantee</key>
              <value></value>
          </field_item>
          <text>
              Delivery Suppl...Finance Department
          </text>
      </field_region>
      ...
  </field_region>
  ```

  </td><td style="vertical-align: top;">

  ![Form Example](examples/form/form_02.png)

  </td></tr></table>
</details>

<details>
  <summary>Use of form headings</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_03.png)

  ```xml
  <field_region>
    <field_heading>Information about you</field_heading>
    <field_item>
        <key>
            \*Family Name (Last Name)
        </key>
        <value>staar</value>
    </field_item>
    <field_item>
        <key>\*Given Name (First Name)</key>
        <value>peter</value>
    </field_item>
    <field_item>
        <key>\*Middle Name (if applicable)</key>
        <value>WJ</value>
    </field_item>
    <field_item>
        <key>I am in the United States as a:</key>
        <text><checkbox class="unselected"/>Visitor</text>
        <text><checkbox class="unselected"/>Student</text>
        <text><checkbox class="unselected"/>Permanent Resident</text>
        <text><checkbox class="unselected"/>Other (Specify)</text>
        <value></value>
    <field_item>
    <field_item>
        <key>Country of Citizenship</key>
        <value></value>
    </field_item>
    <field_item>
        <key>\*Date of Birth</key>
        <value></value>
    </field_item>
    <field_item>
        <key>Alien Registration Number (A-Number) (if any)</key>
        <value>A-</value>
    </field_item>
    <field_heading>Information About Your Address</field_heading>
    <text>\*Present Physical Address ()No Po Boxes</text>
    <field_item>
        <key>\*Street ... Name</key>
        <value></value>
    </field_item>
    <field_item>
        <key>Apt.</key>
        <checkbox class="unselected"/>
    </field_item>
    <field_item>
        <key>Ste.</key>
        <checkbox class="unselected"/>
    </field_item>
    ...

  </field_region>
  ```

</details>

<details>
  <summary>High density form</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_07.png)

  ```xml
  <field_region>
      <form_heading level="1">M31</field_heading>
      <form_heading level="2">REDDITI DI CAPITALE SOGGETTI AD IMPOSIZIONE SOSTITUTIVA</field_heading>
      <field_item>
        <marker>1</marker>
          <key>Tipo</key>
          <value></value>
      </field_item>
      <field_item>
          <marker>2</marker>
          <key>Codice Stato estero</key>
          <value></value>
      </field_item>
      <field_item>
          <marker>3</marker>
          <key>Ammontare reddito</key>
          <value>,00</value>
      </field_item>
      <field_item>
          <marker>4</marker>
          <key>Aliquota %</key>
          <value></value>
      </field_item>
      <field_item>
          <marker>5</marker>
          <key>Credito IVCA</key>
          <value>,00</value>
      </field_item>
      <field_item>
          <marker>6</marker>
          <key>Proventi particolari</key>
          <value></value>
      </field_item>
      <field_item>
          <marker>7</marker>
          <key>Opzione tassazione ordinaria</key>
          <value></value>
      </field_item>
      <form_heading level="1">M32</field_heading>
      <form_heading level="2">PROVENTI DELLE OBBLIGAZIONI NON ASSOGGETTATI A IMPOSTA SOSTITUTIVA</field_heading>
      <field_item>
          <marker>1</marker>
          <key>Ammontare reddito</key>
          <value>,00</value>
      </field_item>
      <field_item>
          <marker>2</marker>
          <key>Aliquota %</key>
          <value></value>
      </field_item>
      <form_heading level="1">M33</field_heading>
      <form_heading level="2">PROVENTI DERIVANTI DA DEPOSITI IN GARANZIA</field_heading>
      <field_item>
          <marker>1</marker>
          <key>Ammontare reddito</key>
          <value>,00</value>
      </field_item>
      ...
  </field_region>
  ```

</details>

<details>
  <summary>Classical duality between tables and explicit key-values</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_06.png)

  ```xml
  <field_region>
      <field_item>
          <key>Adjusted CVSS v3.1 Score</key>
          <value>10.0</value>
      </field_item>
      <field_item>
          <key>Vector</key>
          <value>AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:H</value>
      </field_item>
      <field_item>
          <key>Likelihood</key>
          <value>Very High</value>
      </field_item>
      <field_item>
          <key>Impact</key>
          <value>Catastrophic</value>
      </field_item>
      <field_heading>
        Affected Systems
      </field_heading>
      <otsl>
      <ched/>IP Address<ched/>Port<ched/>Service<ched/>Version<nl/>
      <fcell/>10.0.0.101<fcell/>80/tcp, 8088/tcp<fcell/>Werkzeug<fcell/>3.0.1<nl/>
      <fcell/>10.0.0.102<fcell/>80/tcp, 8088/tcp<fcell/>Werkzeug<fcell/>3.0.1<nl/>
      <fcell/>10.0.0.103<fcell/>80/tcp, 8088/tcp<fcell/>Werkzeug<fcell/>3.0.1<nl/>
      </otsl>
  </field_region>
  ```

</details>

<details>
  <summary>Values without Keys</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_08.png)

  ```xml
  <heading level="1">QUADRO W - Investimenti e...</heading>
  <heading level="2">SEZIONE I - DATI RELATIVI...</heading>
  <field_region>
      <form_heading level="1">W1</field_heading>
      <field_item>
          <marker>1</marker>
          <key>CODICE TITOLO POSSESSO</key>
          <value></value>
      </field_item>
      <field_item>
          <marker>2</marker>
          <key>TIPO CONTRIBUENTE - IVAFE</key>
          <value></value>
      </field_item>
      ...
      <form_heading level="1">W2</field_heading>
      <field_item>
          <marker>1</marker>
          <value></value>
      </field_item>
      <field_item>
          <marker>2</marker>
          <value></value>
      </field_item>
      <field_item>
          <marker>3</marker>
          <value></value>
      </field_item>
      ...
  </field_region>
  ```

</details>

<details>
  <summary>Another complex form deconstructed into field items</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_09.png)

  <table><tr><td>

  ```xml
  <heading level="1">QUADRO C - Redditi di lavoro...</heading>
  <field_region>
      <form_heading level="1">SEZIONE I - RE...</field_heading>
      <field_item>
          <key>Casi particolari</key>
          <checkbox class="unselected"/>
      </field_item>
      <field_item>
        <key>Codice Stato estero</key>
        <value></value>
      </field_item>
      <form_heading level="2">C1</field_heading>
      <field_item>
          <marker>1</marker>
          <key>TIPO</key>
          <value></value>
      </field_item>
      <field_item>
          <marker>2</marker>
          <key>INDETERMINATO/DETERMINATO</key>
          <checkbox class="unselected"/>
      </field_item>
      <field_item>
          <marker>3</marker>
          <key>REDDITO (punti 1,2,3 CU 2025)</key>
          <value>,00</value>
      </field_item>
      <field_item>
          <marker>4</marker>
          <key>ALTRI DATI</key>
          <checkbox class="unselected"/>
      </field_item>
      <form_heading level="2">C2</field_heading>
      <field_item>
          <marker>1</marker>
          <key>TIPO</key>
          <value></value>
      </field_item>
      <field_item>
          <marker>2</marker>
          <key>INDETERMINATO/DETERMINATO</key>
          <checkbox class="unselected"/>
      </field_item>
      <field_item>
          <marker>3</marker>
          <key>REDDITO (punti 1,2,3 CU 2025)</key>
          <value>,00</value>
      </field_item>
      ...
  ```

  </td><td style="vertical-align: top;">

  ```xml
      ...
      <field_item>
          <marker>4</marker>
          <key>ALTRI DATI</key>
          <checkbox class="unselected"/>
      </field_item>
      <form_heading level="2">C3</field_heading>
      <field_item>
          <marker>1</marker>
          <key>TIPO</key>
          <value></value>
      </field_item>
      <field_item>
          <marker>2</marker>
          <key>INDETERMINATO/DETERMINATO</key>
          <checkbox class="unselected"/>
      </field_item>
      <field_item>
          <marker>3</marker>
          <key>REDDITO (punti 1,2,3 CU 2025)</key>
          <value>,00</value>
      </field_item>
      <field_item>
          <marker>4</marker>
          <key>ALTRI DATI</key>
          <checkbox class="unselected"/>
      </field_item>
      <form_heading level="2">C4</field_heading>
      <form_heading level="3">SOMME PER PREMI...
      </field_heading>
      <field_item>
          <marker>1</marker>
          <key>TIPOLOGIA LIMITE</key>
          <checkbox class="unselected"/>
      </field_item>
      <field_item>
          <marker>2</marker>
          <key>SOMME A TASSAZIONE ORDINARIA</key>
          <value>,00</value>
      </field_item>
      <field_item>
          <marker>3</marker>
          <key>SOMME A IMPOSTA SOSTITUTIVA</key>
          <value>,00</value>
      </field_item>
      ...
  </field_region>
  ```

  </td></tr></table>
</details>

<details>
  <summary>Middle section of a form with A and B choices</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_19_water_damage.png)

  ```xml
  <field_region>
      <field_heading>COCHER LES CASES CONCERNEES</field_heading>
      <field_item>
          <key>La cause du sinistre se situe-t-elle chez vous ?</key>
          <text><checkbox class="unselected"/><marker>A</marker>oui</text>
          <text><checkbox class="unselected"/><marker>A</marker>non</text>
          <text><checkbox class="unselected"/><marker>B</marker>oui</text>
          <text><checkbox class="unselected"/><marker>B</marker>non</text>
      </field_item>
      <field_item>
          <key>Êtes-vous assuré en dégâts des eaux ?</key>
          <text><checkbox class="unselected"/><marker>A</marker>oui</text>
          <text><checkbox class="unselected"/><marker>A</marker>non</text>
          <text><checkbox class="unselected"/><marker>B</marker>oui</text>
          <text><checkbox class="unselected"/><marker>B</marker>non</text>
      </field_item>
      <field_item>
          <key>Si vous êtes occupant et que vous allez déménager avez-vous donné ou reçu congé ?</key>
          <text><checkbox class="unselected"/><marker>A</marker>avant le sinistre</text>
          <text><checkbox class="unselected"/><marker>A</marker>après le sinistre</text>
          <text><checkbox class="unselected"/><marker>B</marker>avant le sinistre</text>
          <text><checkbox class="unselected"/><marker>B</marker>après le sinistre</text>
      </field_item>
      <field_heading>NATURE DES DOMMAGES peinture et/ou papier peint</field_heading>
      <field_item>
          <key>revêtements (sol, mur, plafond)</key>
          <text><checkbox class="unselected"/><marker>A</marker>collés</text>
          <text><checkbox class="unselected"/><marker>A</marker>agrafés ou cloués</text>
          <text><checkbox class="unselected"/><marker>B</marker>collés</text>
          <text><checkbox class="unselected"/><marker>B</marker>agrafés ou cloués</text>
      </field_item>
      <field_item>
          <key>Ces aménagements ont-ils été exécutés à vos frais ?</key>
          <text><checkbox class="unselected"/><marker>A</marker>oui</text>
          <text><checkbox class="unselected"/><marker>A</marker>non</text>
          <text><checkbox class="unselected"/><marker>B</marker>oui</text>
          <text><checkbox class="unselected"/><marker>B</marker>non</text>
      </field_item>
      <field_item>
          <key>Autres dommages immobiliers (carrelage, parquet, plâtrerie...)</key>
          <text><checkbox class="unselected"/><marker>A</marker></text>
          <text><checkbox class="unselected"/><marker>B</marker></text>
      </field_item>
      <field_item>
          <key>Objets mobiliers</key>
          <text><checkbox class="unselected"/><marker>A</marker></text>
          <text><checkbox class="unselected"/><marker>B</marker></text>
      </field_item>
      <field_item>
          <key>Matériels ou marchandises</key>
          <text><checkbox class="unselected"/><marker>A</marker></text>
          <text><checkbox class="unselected"/><marker>B</marker></text>
      </field_item>
      <field_item>
          <key>Autres dommages</key>
          <value><marker>A</marker><hint>(à préciser)</hint></value>
          <value><marker>B</marker><hint>(à préciser)</hint></value>
      </field_item>
  </field_region>
  ```

</details>

<details>
  <summary>Tabular form with strong 2D value relationship</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_17_tabular_form_with_many_elements.png)

  ```xml
  <otsl>
  <srow>Beiträge zur Altersvorsorge<srow>52</lcel></srow><nl>
  <fcel/><ched/>Steuerpflichtige Person / Ehemann / Person A<ched/>Ehefrau / Person B<fcel/> <nl>
  <fcel/>Arbeitnehmeranteil laut Nr. 23 a / b der Lohnsteuerbescheinigung<fcel/>*FORM1*,-<fcel/>*FORM2*,-<fcel/>@<nl>
  <fcel/>Beiträge zur landwirtschaftlichen Alterskasse; zu berufsständ...<fcel/>*FORM3*,-<fcel/>*FORM4*,-<fcel/> <nl>
  <fcel/>Beiträge zu gesetzlichen Rentenversicherungen...<fcel/>*FORM5*,-<fcel/>*FORM6*,-<fcel/> <nl>
  <fcel/>Erstattete Beiträge und / oder steuerfreie Zuschüsse zu den...<fcel/>*FORM7*,-<fcel/>*FORM8*,-<fcel/>@<nl>
  ...
  </otsl>
  ...
  *FORMS referred above:
  *FORM1*: <field_item><key>300</key><value></value><hint>EUR</hint></field_item>
  *FORM2*: <field_item><key>400</key><value></value><hint>EUR</hint></field_item>
  *FORM4*: <field_item><key>401</key><value></value></field_item>
  *FORM5*: <field_item><key>302</key><value></value></field_item>
  *FORM3*: <field_item><key>301</key><value></value></field_item>
  *FORM6*: <field_item><key>402</key><value></value></field_item>
  *FORM7*: <field_item><key>309</key><value></value></field_item>
  *FORM8*: <field_item><key>409</key><value></value></field_item>
  ```

</details>

<details>
  <summary>Mix table and form elements</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_15_large_key.png)

  ```xml
  ...
  <heading>Part III</heading>
  <text>Figure Your Credit</text>
  <text>10</text>
  <otsl>
  <ched/>If you checked (in Part l):<ched/>Enter<nl>
  <fcel/>Box 1, 2, 4, or 7<fcel/>$5,000<nl>
  <fcel/>Box 3, 5, or 6<fcel/>$7,500<nl>
  <fcel/>Box 8 or 9<fcel/>$3,750<nl>
  </otsl>
  <field_item><key>10</key><value></value></field_item>
  <text>11 If you checked (in Part I):</text>
  <list class="unordered">
      <list_text>Box 6, add $5,000 to the taxable...</list_text>
      <list_text>Box 2, 4, or 9, enter your taxable...</list_text>
      <list_text>BBox 5, add your taxable disabilit...</list_text>
  </list>
  <field_item><key>11</key><value>.</value></field_item>
  <picture><class>pictogram</class></picture>
  <text>For more details on what to include on line 11...</text>
  <text>12 If you completed line 11, enter the smaller...</text>
  <field_item><key>12</key><value>74,992</value></field_item>
  ...
  ```

</details>

<details>
  <summary>Key-value pair in the wild</summary>

  <!-- blank line after <summary> is important -->

  ![Form Example](examples/form/form_20_key_value_pair_in_the_wild.png)

  ```xml
  ...
  <field_region>
    <field_item>
      <key>Source</key>
      <value>www.pansi.org.uk and ... projections).</value>
    </field_item>
  </field_region>
  ...
  ```

</details>

Detailed examples can be seen here: [Form Examples](/examples/form/form-examples.md)

### Fields

Fields can be used for representing key-value data in a flexible structure where keys and values may be separated by other content or organized in complex layouts.

#### Field Elements

| Element | Description |
|---------|-------------|
| `field_region` | Container for a region containing field items and related content |
| `field_item` | Container that associates keys with values; may contain 0-1 `key` and 0-many `value` elements as descendants |
| `field_heading` | Heading within a field region, with optional level N ≥ 1 |

#### Field Structure Rules

- A `field_region` must contain at least one `field_item` as a descendant (not necessarily a direct child)
- A `field_item` may contain 0 or 1 `key` element as a descendant
- A `field_item` may contain 0 or more `value` elements as descendants
- Values within a `field_item` are implicitly associated with the `key` in that item
- A `field_heading` should have a `field_region` as an ancestor
- Field elements can contain any other DocLang elements (text, pictures, lists, etc.)

#### Field Examples

Basic field region with simple key-value pairs:

```xml
<field_region>
  <field_item>
    <key>Name:</key>
    <value>John Smith</value>
  </field_item>
  <field_item>
    <key>Date of Birth:</key>
    <value>1985-03-15</value>
  </field_item>
  <field_item>
    <key>Address:</key>
    <value>123 Main Street, Anytown, USA</value>
  </field_item>
</field_region>
```

Field region with headings and complex layout:

```xml
<field_region>
  <field_heading level="1">Personal Information</field_heading>

  <field_item>
    <text><key>Full Name:</key></text>
    <text><value>Jane Doe</value></text>
  </field_item>

  <field_item>
    <text><key>Email:</key></text>
    <text><value>jane.doe@example.com</value></text>
  </field_item>

  <field_heading level="2">Employment Details</field_heading>

  <field_item>
    <text><key>Company:</key></text>
    <text><value>Acme Corporation</value></text>
  </field_item>

  <field_item>
    <text><key>Position:</key></text>
    <text><value>Senior Engineer</value></text>
  </field_item>
</field_region>
```

Field item with multiple values:

```xml
<field_region>
  <field_item>
    <key>Phone Numbers:</key>
    <value>+1-555-0100 (Home)</value>
    <value>+1-555-0101 (Work)</value>
    <value>+1-555-0102 (Mobile)</value>
  </field_item>
</field_region>
```

Field item without a key (value-only):

```xml
<field_region>
  <field_heading>Additional Notes</field_heading>
  <field_item>
    <value>This is a standalone value without an explicit key.</value>
    <value>Multiple values can be provided.</value>
  </field_item>
</field_region>
```

Fillable fields with hints:

```xml
<field_region>
  <field_heading>Application Form</field_heading>

  <field_item>
    <key>Full Name:</key>
    <value class="fillable"></value>
    <hint>Enter your first and last name</hint>
  </field_item>

  <field_item>
    <key>Date of Birth:</key>
    <value class="fillable"></value>
    <hint>Format: YYYY-MM-DD</hint>
  </field_item>

  <field_item>
    <key>Email Address:</key>
    <value class="fillable"></value>
    <hint>example@domain.com</hint>
  </field_item>

  <field_item>
    <key>Status:</key>
    <value class="read_only">Pending Review</value>
  </field_item>
</field_region>
```

Field region with mixed content:

```xml
<field_region>
  <location value="50"/><location value="100"/>
  <location value="500"/><location value="400"/>

  <field_heading level="1">Product Specifications</field_heading>

  <text>The following specifications apply to Model XYZ-2000:</text>

  <field_item>
    <key>Dimensions:</key>
    <value>10cm × 15cm × 5cm</value>
  </field_item>

  <field_item>
    <key>Weight:</key>
    <value>250g</value>
  </field_item>

  <picture>
    <uri>assets/product-diagram.png</uri>
    <caption>Product diagram showing key components</caption>
  </picture>

  <field_item>
    <key>Materials:</key>
    <list class="unordered">
      <list_text><marker>•</marker><value>Aluminum alloy frame</value></list_text>
      <list_text><marker>•</marker><value>Tempered glass display</value></list_text>
      <list_text><marker>•</marker><value>Silicone rubber grips</value></list_text>
    </list>
  </field_item>
</field_region>
```

### Split structure

We can capture content that is split (e.g. across columns or across pages) using the `<thread id="N"/>` token, where `N` is a unique identifier.

The basic structure is shown below, e.g. for a `text` tag:

```xml
<text>
  <thread id="1"/>
  This text item starts here
</text>
...
<text>
  <thread id="1"/>
  and continues here.
</text>
```

<details>
  <summary>Cross-column structure example</summary>

  <!-- blank line after <summary> is important -->

![inline-00](./examples/inline/inline_00.png)

Each block that has location information is a top-level tag of the corresponding label, e.g. "text".

Top-level tags which belong to the same item should have the same thread token.

```xml
<text>
    <loc_10/><loc_20/><loc_30/><loc_40/>
    <thread id="1"/>
    where τ<subscript>x,y,z</subscript> are the Pauli matrices acting
    on Nambu space. We consider a circular-shaped boundary, the nor-
</text>

<caption>
    <loc_15/><loc_25/><loc_35/><loc_45/>
    FIG. 3. The modules of the inner product of two MES spinors
    <formula>...<formula/>
    ...
</caption>

<text>
    <loc_20/><loc_30/><loc_40/><loc_50/>
    <thread id="1"/>
    mal direction of the boundary tangent for arbitrary angle θ is
    <formula>ˆx⊥ = (cos θ, sin θ)</formula>
    . Next, we assume an ansatz for the edge state wave function at θ as
	<formula>Ψu/l(x⊥) =eλx⊥ eik∥ x∥ ξu/l </formula>
	with
	<formula>k∥ = sin θkx − cos θky</formula>
	Here, |ξu⟩ and |ξl⟩ represent the spinors ...  of the chiral MESs with
	<formula>φu = 0</formula>
    and
	<formula>φl = φ:</formula>
</text>
```
</details>

<details>
  <summary>Cross-page structure example</summary>

  <!-- blank line after <summary> is important -->

![cross-page-00](./examples/cross_page/cross_page_00.png)

The scenario in the above figure is represented as follows:

```xml
...
<text>
    <loc_10/><loc_20/><loc_30/><loc_40/>
    Our multi-faceted DE&I program includes the following initiatives:
</text>

<list class="unordered">
    <thread id="1"/>
    <list_text>
        <loc_15/><loc_25/><loc_35/><loc_45/>
        Mentorships and internship programs featuring diverse employees and students
    </list_text>
    ...
    <list_text>
        <loc_20/><loc_30/><loc_40/><loc_50/>
        Build Science, Technology, Engineering and Mathematics (STEM) employee candidate pipeline via involvement with:
        <list class="unordered">
            <list_text>
                <loc_25/><loc_35/><loc_45/><loc_55/>
                Historically Black Colleges and Universities (HBCUs) site visits and career fairs
            </list_text>
            ...
            <list_text>
                <loc_30/><loc_40/><loc_50/><loc_60/>
                San Diego Squared (STEM-focused nonprofit organization connecting underrepresented student to the power
                of STEM by providing access to education, mentorship and resources to develop STEM careers)
            </list_text>
        <list>
    </list_text>
<list>

<page_footer><loc_35/><loc_45/><loc_55/><loc_65/>16 Neurocrine Biosciences</page_footer>

<page_break/>

<list class="unordered">
    <thread id="1"/>
    <list_text>
        <loc_40/><loc_50/><loc_60/><loc_70/>
        Build upon DE&I employee education initiatives including:
        ...
    </list_text>
    ...
<list>
...
```
</details>

<details>
  <summary>Split table example</summary>

  <!-- blank line after <summary> is important -->

The table shown on the left may be split across pages, e.g. as shown on the middle. The figure on the right visualizes
the thread elements (more details further below):

<table style="min-width: 1800px">
    <tr>
        <td>
            Original table:
            <br />
            <img src="./examples/split_tables/original_table.png" height="900" width="644" />
        </td>
        <td>
            Table split across pages:
            <br />
            <img src="./examples/split_tables/split_table.png" height="900" width="644" />
        </td>
        <td>
            Table threads:
            <br />
            <img src="./examples/split_tables/table_threads.png" height="900" width="644" />
        </td>
    </tr>
</table>

The scenario in the above figure is represented below.

- We introduce a new horizontal thread token, `h_thread`, which is used to capture table content that spans pages sidewise,
similarly to the usual thread tokens `thread`.
- Only the content that is visible within the page is included in the OTSL token (e.g. see "2025 d").
- When thread linking is resolvable through `ucel`/`lcel` or `h_thread`, the `thread` token is not used, as it would be redundant.
- When thread linking must be captured, we capture it the earliest possible, i.e. we don't wait for the bottom-most cell
to be reached to add the thread for "Europe" in the example above.

```xml
...
<!-- page 1: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <thread id="1"/>
        <h_thread id="1"/>

        <ecel/>                             <ecel/>                      <ecel/><nl/>
        <ecel/>                             <ched/>Continent             <ched/>Country<nl/>
        <rhed/><thread id="2"/>             <rhed/>Asia                  <rhed/>Japan<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 2: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <thread id="1"/>
        <h_thread id="2"/>

        <rhed/><thread id="2"/>G7 member    <rhed/><thread id="3"/>Europe        <rhed/>France<nl/>
        <ucel/>                             <ucel/>                            <rhed/>Germany<nl/>
        <ucel/>                             <ucel/>                            <rhed/>Italy<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 3: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <thread id="1"/>
        <h_thread id="3"/>

        <rhed/><thread id="2"/>             <rhed/><thread id="3"/>            <rhed/>United Kingdom<nl/>
        <ucel/>                             <rhed/>North America               <rhed/>Canada<nl/>
        <ucel/>                             <ucel/>                            <rhed/>United States<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 4: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <h_thread id="1"/>

        <ched/><h_thread id="4"/>2025 d     <lcel/>                            <lcel/><nl/>
        <ched/>GDP (PPP) per capita in USD  <ched/>Currency                    <ched/><h_thread id="5"/>Key l<nl/>
        <fcel/>46,097                       <fcel/>Japanese yen (JPY)          <fcel/>Shigeru Ishiba<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 5: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <h_thread id="2"/>

        <fcel/>54,465                       <fcel/>Euro (EUR)                  <fcel/>Emmanuel Macron<nl/>
        <fcel/>62,830                       <fcel/>Euro (EUR)                  <fcel/>Friedrich Merz<nl/>
        <fcel/>53,115                       <fcel/>Euro (EUR)                  <fcel/>Giorgia Meloni<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 6: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <h_thread id="3"/>

        <fcel/>52,518                       <fcel/>Pound sterling (GBP)        <fcel/>Keir Starmer<nl/>
        <fcel/>62,830                       <fcel/>Canadian dollar             <fcel/>Mark Carney<nl/>
        <fcel/>53,115                       <fcel/>United States dollar (USD)  <fcel/>Donald Trump<nl/>
    </otsl>
</table>
<page_break/>

<!-- page 7: -->
<table>
    <otsl><loc_x0/><loc_y0/><loc_x1/><loc_y1/>
        <h_thread id="1"/>

        <ched/><h_thread id="4"/>etails     <lcel/>                            <lcel/><nl/>
        <ched/><h_thread id="5"/>eader      <ched/>Population in millions      <ched/>Area in km2<nl/>
        <fcel/>Prime Minister               <fcel/>125.1                       <fcel/>377,975<nl/>
    </otsl>
</table>
<page_break/>
...
```
</details>

### Formatting

Formatting may be preserved through nested tags or escape sequences:

- Bold, italic, underline, strikethrough, handwriting
- Superscript, subscript
- Hyperlinks
- Text direction markers

Examples of basic formatting:

```xml
<text>
  This text contains <bold>bold</bold>, <italic>italic</italic>,
  <underline>underlined</underline>, and <strikethrough>struck-through</strikethrough> text.
</text>
```

Nested formatting:

```xml
<text>
  You can combine <bold><italic>bold and italic</italic></bold> or
  <underline><bold>underlined and bold</bold></underline> text.
</text>
```

Handwriting formatting (for handwritten annotations or text):

```xml
<text>
  The printed text says "Sign here:" followed by
  <handwriting>John Smith</handwriting> in handwritten form.
</text>
```

Superscript and subscript:

```xml
<text>
  The formula for water is H<subscript>2</subscript>O, and
  Einstein's equation is E=mc<superscript>2</superscript>.
</text>
```

Hyperlinks with URI and optional formatted content:

```xml
<text>
  Visit our <hyperlink><uri>https://www.example.com</uri>website</hyperlink> for more information.
</text>

<text>
  For details, see the <hyperlink><uri>https://docs.example.com/api</uri><bold>API documentation</bold></hyperlink>.
</text>

<text>
  Email us at <hyperlink><uri>mailto:info@example.com</uri>info@example.com</hyperlink>.
</text>
```

The `hyperlink` element contains:
1. A required `uri` child element with the link target
2. Optional text content and/or formatting elements that represent the visible link text

If no text content is provided after the `uri`, implementations should display the URI itself as the link text.

Right-to-left text direction:

```xml
<text>
  This sentence contains <rtl>نص عربي</rtl> (Arabic text) within it.
</text>
```

#### Page Break with Continuation

Page breaks are complex components that interrupt the flow of a document. They can interrupt paragraphs, tables, lists, etc. In general, we follow two rules,

1. If content spans across one (or more) page breaks, add `<thread id="N"/>` to the item and reuse the same `id` in the continuing item.
2. For the follow up content of the page, we follow a reading order and close all open tokens before the `<page_break/>` token is introduced.

An easy example is below,

```xml
<doclang>
  <text><thread id="1"/>This paragraph spans across</text>
  <caption>Some caption</caption>
  <page_break/>
  <text><thread id="1"/>multiple pages.</text>
</doclang>
```

Often, we have more complicated page breaks, in which a (nested) list is split across pages and further interrupted by other semantic elements (think page footers). In this case, we demand that all elements of the first page are added and/or closed **before** the page break and then opened again in the appropriate way after the page break, with the intent that the content in between the page breaks is a valid DocLang tree.

A more complicated example is shown below in which we break the content of a list-item,

```xml
<doclang>
  <list class="ordered">
    <thread id="1"/>
    <list_text>First item</list_text>
    <list_text><thread id="2"/>Second </list_text>
    ...
  </list>
  <page_footer>...</page_footer>
  <page_break/>
  <list class="ordered">
    <thread id="1"/>
    <list_text><thread id="2"/>item</list_text>
  </list>
  ...
</doclang>
```

Above, `<thread id="1"/>` captures that the list itself is split, while `<thread id="2"/>` captures that a particular
list item is split.

For tables that are broken across pages, we need to introduce two differnt tokens, namely the `<continue_col id=.../>` and `<continue_row id="..."/>`. Same principle applies, if the OTSL starts/ends with any of these tokens, we know the the tables needs to be merged.

## Implementation Requirements

### Parser Requirements

A conforming DocLang parser SHALL:

1. **Syntax Validation**: Recognize all tokens defined in this standard
2. **Geometric Processing**: Handle coordinate and bounding box elements correctly
3. **Version Support**: Process version information and apply appropriate parsing rules
4. **Hierarchy Validation**: Enforce parent-child relationship rules
5. **Continuation Handling**: Correctly link continued content across page breaks
6. **Error Reporting**: Provide meaningful error messages for invalid documents

### Serializer Requirements

A conforming DocLang serializer SHALL:

1. **Valid Output**: Generate syntactically correct DocLang documents
2. **Coordinate Normalization**: Ensure coordinates fit within specified resolution
3. **Structure Preservation**: Maintain element hierarchy and relationships
4. **Version Specification**: Include appropriate version information
5. **Continuation Integrity**: Ensure continuation tokens are properly paired

### Validation Rules

#### Required Structure Validation

- Root element must be `<doclang>`
- List items must appear only within list groupings
- OTSL tokens must appear only within `<otsl>` elements
- Continuation tokens must be properly paired

#### Geometric Validation

- Origin: The coordinate origin is the bottom-left corner of the page.
- Normalization: Each `location` value is an integer within [0, resolution]; per-token `resolution` overrides `metadata.default_resolution`, else use 512×512.
- Point: Exactly 2 consecutive `location` tokens are required (x, then y).
- Bounding box: Exactly 4 consecutive `location` tokens are required in order x0, y0, x1, y1, with x0 ≤ x1 and y0 ≤ y1.
- Rotated rectangle: Exactly 8 consecutive `location` tokens are required in order x0, y0, x1, y1, x2, y2, x3, y3; the segment (x0, y0)→(x1, y1) lies along the bottom edge in reading order.
- Geometric elements should appear in reading order when possible.

#### Temporal Validation

- Components: Timestamps with second-level precision are encoded with `hour`, `minute`, and `second` tokens in strict order. Timestamps with sub-second precision are encoded with `hour`, `minute`, `second` and `centisecond` tokens in strict order.
- Ranges: `hour.value` is an integer in `[0, 99]`; `minute.value` is an integer in `[0, 59]`; `second.value` is an integer in `[0, 59]`; `centisecond.value` is an integer in `[0, 99]`.
- Point with second-level precision: Exactly 3 consecutive tokens are required (hour, then minute, then second).
- Point with sub-second precision: Exactly 4 consecutive tokens are required (hour, then minute, then second, then centisecond).
- Interval with second-level precision: Exactly 6 consecutive tokens are required: start triplet followed by end triplet.
- Interval with sub-second precision: Exactly 8 consecutive tokens are required: start quadruplet followed by end quadruplet.
- Normalization: Out-of-range carry is not allowed; producers MUST pre-normalize values (e.g., 61 minutes becomes 1 hour and 1 minute).
- Monotonicity (intervals): End time MUST be greater than or equal to start time when converted to total seconds.
- Placement: Timestamp tokens MAY only appear on block-level elements and MUST precede textual content and inline formatting when present.
- Coexistence: When both geometric and temporal tokens are present, both appear before content; relative order has no semantic effect.
- Interpretation: Values are relative to a media timeline (not wall-clock), so dates/time zones do not apply.

#### Content Validation

- Text content must be valid Unicode (excluding null character)
- Version strings must follow semantic versioning format
- Classification values should use standard vocabularies where applicable

## Extensibility

### Future Token Addition

New tokens may be added in minor version updates following these rules:

1. New semantic tokens must specify content type (text or structural)
2. New grouping tokens must define allowed children
3. New structural tokens must specify usage context
4. Backward compatibility must be maintained

### Custom Classifications

The `<class>` token supports extensible vocabularies:

- **Programming languages**: Python, JavaScript, C++, etc.
- **Chart types**: bar_chart, pie_chart, line_chart, scatter_plot, etc.
- **Image types**: photograph, diagram, screenshot, icon, logo, etc.

## Bibliography

1. SmolDocling: An ultra-compact vision-language model for end-to-end multi-modal document conversion
2. Optimized Table Tokenization for Table Structure Recognition
3. DoclingDocument API Specification
4. W3C XML 1.0 Specification (Fifth Edition)
5. W3C HTML5 Specification
6. ISO 32000-2:2020 (PDF 2.0)
7. ISO 8601
8. Semantic Versioning 2.0.0 (semver.org)

## Appendix A: Complete Token Reference

### Token Table

| # | Category | Token | Self-Closing [Yes/No] | Parametrized [Yes/No] | Attributes | Description |
|---|----------|-------|-----------------------|-----------------------|------------|-------------|
| 1 | Root Elements | `doclang` | No | Yes | `version` | Root container; optional semantic version `version`. |
| 2 | Special Elements | `page_break` | Yes | No | — | Page delimiter. |
| 3 |  | `time_break` | Yes | No | — | Temporal segment delimiter. |
| 4 | Metadata Containers | `head` | No | No | — | Document-level metadata container. |
| 5 |  | `meta` | No | No | — | Component-level metadata container. |
| 6 | Geometric Tokens | `location` | Yes | Yes | `value`, `resolution?` | Geometric coordinate; `value` in [0, res]; optional `resolution`. |
| 7 | Temporal Tokens | `hour` | Yes | Yes | `value` | Hours component; `value` in [0, 99]. |
| 8 |  | `minute` | Yes | Yes | `value` | Minutes component; `value` in [0, 59]. |
| 9 |  | `second` | Yes | Yes | `value` | Seconds component; `value` in [0, 59]. |
| 10 |  | `centisecond` | Yes | Yes | `value` | Centiseconds component; `value` in [0, 99]. |
| 11 | Semantic Tokens | `title` | No | No | — | Document or section title (content). |
| 12 |  | `heading` | No | Yes | `level` | Section header; `level` (N ≥ 1). |
| 13 |  | `text` | No | No | — | Generic text content. |
| 14 |  | `caption` | No | No | — | Caption for floating/grouped elements. |
| 15 |  | `footnote` | No | No | — | Footnote content. |
| 16 |  | `page_header` | No | No | — | Page header content. |
| 17 |  | `page_footer` | No | No | — | Page footer content. |
| 18 |  | `watermark` | No | No | — | Watermark indicator or content. |
| 19 |  | `picture` | No | No | — | Block image/graphic; at most one of `base64`/`uri`; may include `meta` for classification; `otsl` may encode chart data. |
| 20 |  | `formula` | No | No | — | Mathematical expression block. |
| 21 |  | `code` | No | No | — | Code block. |
| 22 |  | `list_text` | No | No | — | Leading text of a list item, including any available marker or checkbox information. |
| 23 |  | `field_region` | No | No | — | Field region container; contains at least one `field_item` as descendant. |
| 24 |  | `field_item` | No | No | — | Field item container; may contain 0-1 `key` and 0-many `value` elements as descendants. |
| 25 |  | `field_heading` | No | Yes | `level?` | Field heading within a field region; optional `level` (N ≥ 1). |
| 26 |  | `hint` | No | No | — | Hint for a fillable field (format/example/description). |
| 31 | Grouping Tokens | `group` | No | Yes | `type?` | Generic group; no `location` tokens; associates composite content (e.g., captions/footnotes). |
| 32 |  | `list` | No | Yes | `class` in {`unordered`, `ordered`}; defaults to `unordered` | List container. |
| 27 |  | `floating_group` | No | Yes | `class` in {`table`,`picture`,`code`} | Floating container that groups a floating component with its caption, footnotes, and metadata; no `location` tokens. |
| 34 | Formatting Tokens | `bold` | No | No | — | Bold text. |
| 35 |  | `italic` | No | No | — | Italic text. |
| 36 |  | `underline` | No | No | — | Underlined text. |
| 37 |  | `strikethrough` | No | No | — | Strike-through text. |
| 38 |  | `handwriting` | No | No | — | Handwritten text. |
| 39 |  | `superscript` | No | No | — | Superscript text. |
| 40 |  | `subscript` | No | No | — | Subscript text. |
| 41 |  | `rtl` | No | No | — | Right-to-left text direction. |
| 42 |  | `hyperlink` | No | No | — | Hyperlink; contains required `uri` child and optional formatted text content. |
| 43 |  | `inline` | No | Yes | `class` in {`formula`,`code`,`picture`} | Inline content; if `class="picture"`, may include one of `base64` or `uri`. |
| 44 |  | `br` | Yes | No | — | Line break. |
| 45 | Structural Tokens (OTSL) | `otsl` | No | No | — | Table structure container. |
| 46 |  | `fcel` | Yes | No | — | New cell with content. |
| 47 |  | `ecel` | Yes | No | — | New cell without content. |
| 48 |  | `ched` | Yes | No | — | Column header cell. |
| 49 |  | `rhed` | Yes | No | — | Row header cell. |
| 50 |  | `corn` | Yes | No | — | Corner header cell. |
| 51 |  | `srow` | Yes | No | — | Section row separator cell. |
| 52 |  | `lcel` | Yes | No | — | Merge with left neighbor (horizontal span). |
| 53 |  | `ucel` | Yes | No | — | Merge with upper neighbor (vertical span). |
| 54 |  | `xcel` | Yes | No | — | Merge with left and upper neighbors (2D span). |
| 55 |  | `nl` | Yes | No | — | New line (row separator). |
| 56 | Continuation Tokens | `thread` | Yes | Yes | `id` | Continuation marker for split content; reuse same `id` across parts. |
| 57 |  | `h_thread` | Yes | Yes | `id` | Horizontal stitching marker for split tables; reuse same `id`. |
| 58 | Binary Data Tokens | `base64` | No | No | — | Embedded binary data (base64). |
| 59 |  | `uri` | No | No | — | External resource reference. |
| 60 | Content Tokens | `marker` | No | No | — | List/field marker content. |
| 61 |  | `checkbox` | Yes | Yes | `class` in {`unselected`, `selected`}; defaults to `unselected` | Checkbox status. |
| 62 |  | `facets` | No | No | — | Container for application-specific derived properties. |
| 63 |  | `hint` | No | No | — | Hint for fillable field; recommended within `field_item` context. |
| 64 | Structural Tokens (Field) | `key` | No | No | — | Field item key. |
| 65 |  | `value` | No | Yes | `class` in {`read_only`, `fillable`}; defaults to `read_only` | Field item value; `read_only` for pre-filled values, `fillable` for editable fields. |

### Metadata Sub-elements

| # | Token | Self-Closing [Yes/No] | Parametrized [Yes,No] | Description |
|---|-------|-----------------------|-----------------------|-------------|
| 1 | `title` | No | No | Document title (metadata context). |
| 2 | `author` | No | No | Author entry; may contain `affiliation` children and text. |
| 3 | `affiliation` | No | No | Author affiliation; child of `author`. |
| 4 | `date` | No | No | Document date in ISO 8601 format (e.g., YYYY-MM-DD). |
| 5 | `language` | No | Yes | Language code (ISO 639-3); attributes: `classifier`, `score`. |
| 6 | `default_resolution` | Yes | Yes | Default coordinate resolution; attributes: `width`, `height`. |
| 7 | `page_size` | Yes | Yes | Original page size; attributes: `width`, `height`; optional `page_no` starts at 1. |
| 8 | `document_quality` | No | Yes | Quality score; attribute: `classifier`; content is a number [0,1]. |
| 9 | `document_readability` | No | Yes | Readability score; attribute: `classifier`; content is a number [0,1]. |
| 10 | `general_topic` | No | Yes | Topic label; attributes: `topic_taxonomy`, `classifier`, `score`. |
| 11 | `document_hash` | No | Yes | Document hash value; attribute: `hash_function` (e.g., SHA-256). |
| 12 | `custom_attribute` | No | Yes | Custom key/value; attributes: `key`, `name`; content is value. |
| 13 | `processing_tool` | No | No | Name of the processing tool (e.g., docling). |

### Governance Metadata Sub-elements

| # | Token | Self-Closing [Yes/No] | Parametrized [Yes/No] | Description |
|---|-------|-----------------------|-----------------------|-------------|
| 1 | `licenses` | No | No | Container for one or more `license` entries. |
| 2 | `license` | No | No | License URL, SPDX identifier, or text. |
| 3 | `data_classification` | No | No | Container for one or more `data_class` entries. |
| 4 | `data_class` | No | No | Organization-defined data sensitivity class. |
| 5 | `acceptable_use` | No | No | Container for one or more `purpose` entries describing acceptable use. |
| 6 | `purpose` | No | No | A specific acceptable use purpose description. |
| 7 | `stewardship` | No | No | Container for one or more `steward` entries. |
| 8 | `steward` | No | No | Governance contact entry; may include `name`, `contact`, and `org`. |
| 9 | `name` | No | No | Steward’s person or team name. |
| 10 | `contact` | No | No | Steward contact information (e.g., email or URI). |
| 11 | `org` | No | No | Steward’s organization. |
| 12 | `access_policy` | No | No | Container for one or more `policy` entries defining access rules. |
| 13 | `policy` | No | No | Policy entry; may include `ref`, `roles`. Reused under multiple governance parents. |
| 14 | `ref` | No | No | Reference to policy documentation (e.g., URL or identifier). |
| 15 | `roles` | No | No | Container for one or more `role` entries. |
| 16 | `role` | No | No | Role name allowed by policy (organization-defined semantics). |
| 17 | `retention_policy` | No | No | Container for one or more `policy` entries defining retention. |
| 18 | `retention_period` | No | Yes | Retention duration; attribute: `unit` (e.g., year, month, day); content is a number. |
| 19 | `deletion_method` | No | No | Method for deletion (e.g., secure erasure approach). |
| 20 | `documentation` | No | No | Free-text or URI documenting retention actions. |
| 21 | `compliance_requirements` | No | No | Container for one or more `compliance_req` entries. |
| 22 | `compliance_req` | No | No | Compliance framework requirement (e.g., GDPR, HIPAA, PCI DSS). |

## Appendix B: Escape entities

TBA
