# ISO XXX - DocTags: Universal Document Markup Format (Revised)

## Foreword

This document was prepared by

- Peter Staar,
- Maroun touma,
- Panos Vagenas,
- Maksym Lysak,
- Nikolaos Livathinos
- Santosh Borse,
- Yousaf Shah,
- Michele Dolfi
- (FILL IN!).

This International Standard specifies the DocTags format, a universal markup language for representing structured document content with semantic, geometric, and formatting information.

## Introduction

The proliferation of digital documents across diverse formats (PDF, HTML, Word, etc.) has created significant challenges in document processing, conversion, and understanding. These were mainly designed for efficient rendering and often result in loss of semantic information, structural relationships, or geometric context during document conversion.

DocTags addresses these challenges by providing a minimalist, unambiguous markup format that:

- Preserves complete document structure and semantics
- Maintains geometric and layout information when appropriate
- Supports complex document components including tables, formulas, code, nested lists, and charts
- Enables lossless round-trip conversion between formats regarding content
- Maintains token efficiency by defining controlled vocabulary of tags and attributes
- Eliminates ambiguity by enforcing a well defined set of tags with restricted, non generic usage ( and preserves semantic clarity )

This standard builds upon research in document understanding and is intended to represent the content of a document as accurately as possible while maintaining implementation simplicity.

## Scope

This International Standard specifies:

- The syntax and semantics of the DocTags markup language
- Rules for encoding document structure, content, and metadata
- Mechanisms for representing geometric layout and pagination
- Methods for preserving formatting and text direction
- Specifications for complex document components (tables, charts, formulas, code, forms)
- Requirements for conforming implementations

## Motivation

The motivation for this new markup language is twofold,

1. It is created from the ground up to be able to represent complex, multimodal content with visual grounding in plain text
2. It is created with the express purpose to be compatible from the start with LLM tokenizers, i.e. use a structure that maps naturally (== a 1-to-1 mapping between DocTags tokens and LLM tokens) and efficiently (== minimal token count).

As a consequence of point 2, we need to ensure that there is limited number or semantic tags and attributes. In general, we intend that the number of semantic tokens should not exceed 1000. The latter is not a strong bound, but rather a direction.

There is an exception for the meta-data. The meta-data is not intended to be used by the LLM's, so it is in general possible to have a more expanded set of protected keys. Nevertheless, we do want to normalize as much as possible the representation.

Such requirements preclude us from using existing markup languages such as Markdown (incomplete scope), HTML (not concise enough), LaTeX (ambiguity of representation) etc.

<figure style="text-align: left">
    <img src="resources/html_v_otsl.png"
         alt="HTML vs OTSL" style="width:700px">
    <figcaption>Example in pure table structure representation, omitting content of cells, when comparing HTML to Doctags (OTSL tags). HTML sequence is both longer and uses more tokens than Doctags/OTSL</figcaption>
</figure>

<figure style="text-align: left">
    <img src="resources/doctags_example.png"
         alt="HTML vs OTSL" style="width:1000px">
    <figcaption>Examples of real-world document fragments and their Doctags representation</figcaption>
</figure>

## Terminology

Abstract concepts:

- **document component**: A cohesive and meaningful part of the document, e.g. a table or a bold piece of text.

From XML:

- **element**: An XML element.
- **attribute**: An XML attribute.
- **tag**: An XML tag: can be a start-tag, an end-tag, or an empty-element tag (AKA self-closing tag).

From HTML:

- **flow content** AKA **block-level element**: An element that is meant to be interpreted or displayed as a block, i.e. starting on a new line and occupying the full width of its container; a typical HTML example is the `p` element (paragraph).
- **phrasing content** AKA **inline element**: An element that can be used within flow content to shape its in-line structure; a typical HTML example is the `span` element.

DocTags:

- **(DocTags) token**: A low-level symbol capturing some aspect of a document or of a component thereof, expressed as a tag.

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

Aiming at LM-friendliness, in such cases, the ISO DocTags format favors an alternative representation of property semantics, namely captured as respective elements leading the content.
The example above could be represented as `<elem><size>250</size><color>#ffeedd</color>foo</elem>`. Depending on the specific properties, self-closing elements are used too.

This representation can reduce the number of tokens, making it easier for language models to learn and predict.

For elements with a strictly limited set of possible property values, attributes are still used.

## Content encoding

The content of the elements is encoded according to the following rules:

- unicode textual content is encoded as utf-8.
- special characters reserved by XML, such as `<` (complete list defined in Appendix B), can be represented:
  - either by escaping with the respective XML entities, e.g. `<` becomes `&lt;`,
  - or using the CDATA section syntax, e.g. raw text `<foo>` can be represented as `<![CDATA[<foo>]]>`

## DocTags Structure

DocTags is a constrained subset of XML with the following characteristics:

- Simplified syntax with a finite set of allowed tags
- Constrained use of attributes on most elements
- Character-based encoding using legal Unicode characters (except Null)
- Standard XML parsing rules apply for markup vs content distinction

DocTags defines the following categories of elements:

- **special**: Elements that establish document scope and pagination, such as `doctag`, `page_break`, and `time_break`.
- **provenance**: Elements that can provide visual or time grounding. The visual grounding is necessary for documents with pagination, the temporal grounding is necessary for audio based documents (music and movies).
	- **spatial**: Elements that capture spatial position as normalized coordinates/bounding boxes (via repeated `location`) anchoring block-level content to the page.
	- **time**: Elements that capture temporal positions using `<hour value={integer}/><minute value={integer}/><second value={integer}/><centisecond value={integer}/>` for a timestamp and a double timestamp for time intervals.
- **semantic**: Block-level elements that convey document meaning (e.g., titles, paragraphs, captions, lists, forms, tables, formulas, code, pictures), optionally preceded by location tokens.
- **formatting**: Inline elements that modify textual presentation within semantic content (e.g., `bold`, `italic`, `strikethrough`, `superscript`, `subscript`, `rtl`, `inline_formula`, `inline_code`, `inline_picture`, `br`).
- **grouping**: Elements that organize semantic blocks into logical hierarchies and composites (e.g., `section`, `list`, `group type=*`) and never carry location tokens.
- **structural**: Sequence tokens that define internal structure for complex constructs (primarily OTSL table layout: `otsl`, `fcel`, `ecel`, `lcel`, `ucel`, `xcel`, `nl`, `ched`, `rhed`, `corn`, `srow`; and form parts like `key`/`value`).
- **content**: Lightweight content helpers used inside semantic blocks for explicit payload and annotations (e.g., `marker`).
- **binary data**: Elements that embed or reference non-text payloads for media—either inline as `base64` or via `uri`—allowed under `picture`, `inline_picture`, or at page level.
- **continuation** tokens: Markers that indicate content spanning pages or table boundaries (e.g., `<thread id="N"/>`, `continue_row`, `continue_col`) to stitch fragmented content.

### Special Elements

These elements have a specific purpose in defining the high-level structure of the document.

#### The `doctag` Element

Every DocTags document is wrapped in a `<doctag>` root element with an optional version specification,
following Semantic Versioning (MAJOR.MINOR.PATCH). When no version is specified, the default is v1.0.0.

Here is an example:

```xml
<doctag version="1.0.0">
  <!-- document content -->
</doctag>
```

#### The `metadata` Element

The document can optionally begin with a `<metadata>` element, which can contain the following optional special elements:

- `version`
- `title`  <!-- NOTE: conflicts with semantic element -->
- `author`, whereby multiple instances are allowed
  - each `author` element can optionally begin with one or more `affiliation` elements
- `date`
- `language`, whereby multiple instances are allowed
- `default_resolution`
- `page_size`, the actual page size. An element without the `page_no` attribute defines the default size for all pages, when `page_no` is specified it is counted from 1.
- `language`, Identifies the document language (e.g., English, German, French, Spanish, Japanese). The content MUST be an [ISO 639-3](https://iso639-3.sil.org/about) language identifier. Optional attributes: `classifier` (the tool/method used, e.g., fastText) and `score` (confidence in [0, 1]). Multiple `language` entries MAY be provided.
- `document_quality`,Content quality assessment score using standard algorithms such as DCLM, gneissweb, etc. where 0<=Scores<=1
- `document_readability`,Indicates how easy a a document can be undertood by a general audiance. Classifier defines known classifier or method used to produce score where 0<=Scores<=1
- `general_topic`,Topic that the document is most likely to fall in such as Science and Technology, Legal, etc. The topics should preferrably come from some taxonomy. Classifier defines the classifier used for classifying into the given topic and score is the confidence score of classifier and 0<=Scores<=1. This can be one or more.
- `document_hash`, Hash of the document, whereas hash_function defines the algorithm used to compute the hash, e.g., SHA2. This can be one or more.
- `custom_attribute`, Any custom attribute that can be added later with its properties in keys and corresponding values. This can be one or more.

Here is an example:

```xml
<doctag>
  <metadata>
    <version>1.2.3</version>
    <author>Author 1 Name</author>
    <author>
      <affiliation>Author 2 Affiliation A</affiliation>
      <affiliation>Author 2 Affiliation B</affiliation>
      Author 2 Name
    </author>
    <date>2024-01-01</date>
    <language classifier="fastText" score="0.7">eng</language>
    <language classifier="fastText" score="0.2">spa</language>
    <document_quality classifier="dclm">0.8</document_quality>
    <document_readability classifier="fastText_readability">0.4</document_readability>
    <general_topic topic_taxonomy="taxonomy" classifier="WatsonNLP" score="0.5">Technology</general_topic>
    <general_topic topic_taxonomy="taxonomy" classifier="WatsonNLP" score="0.5">Math</general_topic>
    <document_hash hash_function="sha256sum"/>75f2db0c6124527bf6dd48440f95fc864a5108d28517633f937923a7d8199185</document_hash>
    <custom_attribute key="hate" name="HAP"/>0.1</custom_attribute>
    <custom_attribute key="abuse" name="HAP"/>0.1</custom_attribute>
    <custom_attribute key="profanity" name="HAP"/>0.1</custom_attribute>
    <default_resolution width="512" height="512"/>
    <page_size width="612" height="792"/>
    <page_size page_no="4" width="792" height="612"/>
    <processing_tool>docling</processing_tool>
  </metadata>
  <!-- document content -->
</doctag>
```

These annotations can provide semantic insights or quality assessments for post processing purpose.

<!-- I think we should allow metadata to be embded into any tag -->


#### The `page_break` Element

A paginated document may be divided into pages using the `<page_break/>` empty-element tag.

Here is an example:

```xml
<doctag>
  <!-- first page content -->
  <page_break/>
  <!-- second page content -->
</doctag>
```

The content between two `<page_break/>` is in itself a doctag document, if it is sandwiched between `<doctag>...</doctag>`.

#### The `time_break` Element

Audio-based documents may be divided into timed segments. These timed segments can be indicated by the `<time_break/>` symbol.

```xml
<doctag>
  <!-- first page content -->
  <time_break/>
  <!-- second page content -->
</doctag>
```

The content between two `<time_break/>` is in itself a doctag document, if it is sandwiched between `<doctag>...</doctag>`.

### Provenance Elements

#### The `location` Element

The `location` element represents spatial information with value (and optional resolution) attributes of the format `<location value="integer" resolution="integer"/>` with 0 <= value <= resolution.

- Single coordinate at (100, 200): `<location value="100"/><location value="200"/>`
- Bounding box with (x0, y0) = (100, 200) and (x1, y1) = (300, 400): `<location value="100"/><location value="200"/><location value="300"/><location value="400"/>`

Coordinate system and encoding rules:

- Origin: The origin of the coordinate system is the bottom-left corner of the page.
- Point: Use exactly 2 consecutive `location` tokens to encode a point; the first token is x, the second is y.
- Bounding box: Use exactly 4 consecutive `location` tokens to encode a bounding box in strict order: x0, y0, x1, y1.
- Rotated rectangle: Use exactly 8 consecutive `location` tokens to encode a (potentially rotated) rectangle in strict order: x0, y0, x1, y1, x2, y2, x3, y3; x0, y0 and x1, y1 lie along the bottom edge in reading order.
- Normalization: Each `location`’s `value` is an integer in `[0, resolution]`; if a `location` specifies a `resolution` attribute it is used for that token, otherwise the `metadata.default_resolution` applies. When neither is available, use `512×512` as the implicit default.
- Connection to page size: The boxes are proportional to the page where they belong, they will not capture the actual size or aspect ratio. Those can be reconstructed with the `page_size` metadata.

The `location` element may only be used in elements which are meant to be interpreted as block-level, as specified further below.

Usage examples:

```xml
<!-- Bounding box on a title -->
<heading level="1">
  <location value="100"/><location value="620"/>
  <location value="900"/><location value="680"/>
  Annual Report
</heading>

<!-- Paragraph anchored by a bounding box -->
<text>
  <location value="120"/><location value="540"/>
  <location value="880"/><location value="520"/>
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
- Coexistence with location: When both spatial `location` tokens and `timestamp` tokens are present, both sets MUST appear before content. The relative order between spatial and temporal tokens has no semantic impact; serializers SHOULD use a consistent order.
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
| `title` | Document or section title |
| `heading` | Section header, with optional level N ≥ 1 |
| `text` | Generic text content |  <!--  TODO: rename to `paragraph` -->
| `caption` | Caption for floating elements |
| `footnote` | Footnote content |
| `page_header` | Page header content |
| `page_footer` | Page footer content |
| `watermark` | Page contains watermark | <!-- watermark can be text or image - do we want to capture that? also do we want to know if watermark is in background or overlay?-->
| `list_item` | List item |
| `form_item` | Form item (with 1 key and 1 or more values as children) |
| `form_header` | Form header |
| `form_text` | Form text |
| `key` | key of the form item: can only be a child of `form_item` |
| `value` | value of the form item: can only be a child of `form_item`  |
| `checkbox selected=true` | Selected checkbox item |
| `checkbox selected=false` | Unselected checkbox item |
| `otsl` | Table structure |
| `formula` | Mathematical expression |
| `code` | Code block |
| `picture` | Image or graphic element; might have a binary data child (`base64` or `uri`) |
| `form` | Form structure |

### Formatting Elements

Formatting elements represent formatting information within the content of a semantic element and are meant to be interpreted as inline elements. Formatting elements can be nested, e.g. `<bold><italic>bold italic</italic></bold>`.

| Token | Description |
|-------|-------------|
| `bold` | Bold text |
| `italic` | Italic text |
| `strikethrough` | Strike-through text |
| `superscript` | Superscript |
| `subscript` | Subscript |
| `rtl` | Right-to-left text direction |
| `inline_formula` | Inline formula |
| `inline_code` | Inline code |
| `inline_picture` | Inline picture; might have a binary data child (`base64` or `uri`) |
| `br`| Line break (empty-element tag) |

### Grouping Elements

These elements organize semantic content into logical structures. Groups can not have any location tokens and are intended to create the semantic tree.

| Element | Description | Allowed Children |
|-------|-------------|------------------|
| `<list ordered=true>` | Numbered list | list\_item, checkbox |
| `<list ordered=false>` | Bulleted list | list\_item, checkbox |
| `<group>` | Generic group enabling e.g. association of caption or footnote with the respective document components | |

**footnote regarding docling-core**: What we currently have as instantiations of `FloatingItem` (e.g., TableItem) should have been groups, as the `FloatingItem` contains captions, the `data structure` (e.g., the `data` in TableItem or the `graph` in FormItem) and the footnotes. As a matter of fact, it is currently even more mis-constructed, since the `ProvenanceItem` of the `TableItem` will in fact point to location of only the table, while the captions and footnotes will have their own `ProvenanceItem`.

### Optimized Table Structure Language (OTSL)

Tabular structure and header semantics in DocTags represented by optimized table-structure language (OTSL) tokens.

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

### Content Tokens

| Token | Description |
|-------|-------------|
| `<marker>`| Marker (eg for in section-header, list-item, etc) |
| `<facets>`| Container meant for application-specific properties for derived information, such as summary, classification label, etc. |

The present standard does not prescribe the specific `facets` content, but a possible instantiation could be:

```xml
<doctag>
  <picture>
    <facets>
      <summary>This image shows the distribution of the various data points in the dataset</summary>
      <class>pie_chart</class>
    </facets>
    <location value="50"/><location value="60"/><location value="450"/><location value="360"/>
    <base64>iVBORw0KGgoAAAANSUhEUgAA...truncated...5ErkJggg==</base64>
  </picture>
</facets>
```

### Continuation Tokens

For content spanning page breaks:

| Token | Description |
|-------|-------------|
| `<thread_N/>` | Special element for capturing content that spans across pages ([example](./examples/cross_page/index.md)) |
| `<h_thread_N/>` | Special element for horizontal stitching of table content ([example](./examples/split_tables/index.md)) |

### Binary Data Elements

Binary data elements encode non-text payloads that semantic content can reference or embed. They can appear directly under a page’s flow (page-level) or as children of elements that carry binary payloads.

- `base64`: Embeds binary data as a base64-encoded string between the tags.
- `uri`: Provides a reference to an external or local resource via a valid URI or filesystem path.

Usage rules:
- Allowed parents: `picture`, `inline_picture`, and page-level flow (i.e., between `page_break` markers) when associating a resource with the current page.
- For `picture` and `inline_picture`, include at most one of `base64` or `uri` as a child.
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
  The logo <inline_picture><uri>assets/logo.png</uri></inline_picture> appears here.
</text>

<!-- Page-level binary payload associated with the current page -->
<page_break/>
<uri>assets/page_2_background.png</uri>
<text>Page 2 content...</text>
```

### Vector graphics Elements

If you want to include vector graphics elements, the doctags allow you to include

1. SVG: enclosed in `<svg> ... </svg>`

## Grammar and Structure Rules

### Simple Document Structure

In the simplest document example, document elements are in a flat list,

```xml
<doctag version="1.0.0">
  <heading level="1">Research Paper Title</heading>
  <heading level="2">Abstract</heading>
  <text>This paper presents...</text>
  <heading level="2">Introduction</heading>
  <text>In recent years...</text>
  <heading level="3">Background</heading>
  <text>Previous work has shown...</text>
</doctag>
```

The user is allowed to add sections or groups as they see fit, but it is not a strong requirement,

```xml
<doctag version="1.0.0">
  <heading level="1">Research Paper Title</heading>

  <section level="1">
    <heading level="2">Abstract</heading>
    <text>This paper presents...</text>
  </section>

  <section level="1">
    <heading level="2">Introduction</heading>
    <text>In recent years...</text>

    <section level="2">
      <heading level="3">Background</heading>
      <text>Previous work has shown...</text>
    </section>
  </section>
</doctag>
```

In case of page-layout information, the coordinates are provided only at the semantic element level. Coordinates are not allowed at the group level.

```xml
<doctag version="1.0.0">
  <heading level="1">
    <location value="10"/><location value="20"/><location value="30"/><location value="40"/>
    Research Paper Title
  </heading>

  <section level="1">
    <heading level="2">
      <location value="10"/><location value="20"/><location value="30"/><location value="40"/>
      Abstract
    </heading>
    <text>
      <location value="10"/><location value="20"/><location value="30"/><location value="40"/>
      This paper presents...
    </text>
  </section>

  <section level="1">
    <heading level="2">Introduction</heading>
    <text>In recent years...</text>

    <section level="2">
      <heading level="3">Background</heading>
      <text>Previous work has shown...</text>
    </section>
  </section>
</doctag>
```

### Code snippets

Code content can appear inline via `inline_code` or as block code via `code`. To classify the programming language of a block, include a `<class>...</class>` child inside `code`. When using groups, place coordinates only on semantic elements (e.g., `caption`, `code`), not on the `group` itself.

Basic inline code

```xml
<text>
  Install with <inline_code>pip install doctags</inline_code> and run.
  For environment checks, use <inline_code>python --version</inline_code>.
  Inline code preserves spacing and punctuation.
  <br/>
  Example path: <inline_code>/usr/local/bin</inline_code>
  <br/>
  Variables like <inline_code>API_KEY</inline_code> should not be committed.
  <br/>
  Use <inline_code>Ctrl+C</inline_code> to stop the server.
  <br/>
  Command substitution: <inline_code>$(echo hello)</inline_code>
  <br/>
  JSON snippet: <inline_code>{"ok":true}</inline_code>
  <br/>
  Escaping: <inline_code>&lt;tag&gt;value&lt;/tag&gt;</inline_code>
  <br/>
  Code fragments can mix with <bold>formatting</bold> seamlessly.
  <br/>
  Use backticks sparingly; DocTags uses explicit tokens instead.
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

All math is authored as LaTeX inside `inline_formula` (inline) or `formula` (block). Do not use `<class>` for math; language classification is not applicable here. The optional `<marker>` child inside `formula` carries the printed equation number or label (e.g., “(1)”, “Eq. 3”). If present, include it as plain text within `<marker>`.

Inline math examples

```xml
<text>
  The famous relation <inline_formula>E = mc^2</inline_formula> connects mass and energy.
  For small x, <inline_formula>\sin x \approx x - x^3/3!</inline_formula> holds.
  The binomial: <inline_formula>(a+b)^n = \sum_{k=0}^n \binom{n}{k} a^{n-k} b^k</inline_formula>.
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

DocTags separates the table’s structure from its surrounding semantics:

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
      <list ordered=false>
        <list_item><marker>•</marker>Ingest</list_item>
        <list_item><marker>•</marker>Process</list_item>
        <list_item><marker>•</marker>Export</list_item>
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
- Rich cells can include any valid DocTags content; keep content immediately after the corresponding cell token.

### Lists

Lists are containers of homogeneous items. Allowed direct children are only `list_item` and `checkbox`. Both can include an optional `<marker>` to hold the printed bullet/number/checkbox symbol. When needed, the `<marker>` may also carry its own `<location>` coordinates to capture where the glyph appears on the page.

Unordered list with optional markers

```xml
<list ordered=false>
  <list_item>
    <marker>•</marker>
    First item with <bold>bold</bold> text
  </list_item>
  <list_item>
    <!-- Marker with its own coordinates -->
    <marker>
      <location value="50"/><location value="110"/><location value="60"/><location value="120"/>
      •
    </marker>
    Second item
  </list_item>
</list>
```

Ordered list; markers are optional and can hold the printed numbering

```xml
<list ordered=true>
  <list_item>
    <marker>1.</marker>
    Install dependencies
  </list_item>
  <list_item>
    <marker>2.</marker>
    Run tests
  </list_item>
  <list_item>
    <!-- No marker provided; numbering can be inferred from order -->
    Ship release
  </list_item>
</list>
```

Checkbox items with selection state; markers optional

```xml
<list ordered=false>
  <checkbox selected=true>
    <marker>[x]</marker>
    Completed task
  </checkbox>
  <checkbox selected=false>
    <marker>[ ]</marker>
    Pending task
  </checkbox>
</list>
```

Nested lists (mixing ordered and unordered)

```xml
<list ordered=true>
  <list_item>
    <marker>1.</marker>
    Setup project
    <list ordered=false>
      <list_item>
        <marker>•</marker>
        Create virtual environment
      </list_item>
      <list_item>
        <marker>•</marker>
        Configure linter
      </list_item>
    </list>
  </list_item>
  <list_item>
    <marker>2.</marker>
    Implement features
  </list_item>
</list>
```

Page breaks and continuation

Lists can span multiple pages. Use `<thread id="..."/>` to indicate continuation. You may thread the whole list and, if a particular `list_item` is broken, also thread the item itself.

List split across pages

```xml
<list ordered=true>
  <thread id="L1"/>
  <list_item><marker>1.</marker>First item</list_item>
  <list_item><marker>2.</marker>Second item</list_item>
</list>
<page_break/>
<list ordered=true>
  <thread id="L1"/>
  <list_item><marker>3.</marker>Third item</list_item>
</list>
```

Single list-item broken by a page break

```xml
<list ordered=false>
  <thread id="L2"/>
  <list_item>
    <thread id="I7"/>
    <marker>•</marker>
    This item starts on page 1 and continues
  </list_item>
</list>
<page_break/>
<list ordered=false>
  <thread id="L2"/>
  <list_item>
    <thread id="I7"/>
    on page 2 until it ends.
  </list_item>
</list>
```

Notes
- Only `list_item` and `checkbox` are valid as children of `list`.
- `<marker>` is optional on both `list_item` and `checkbox`. Include it when the printed glyph/number is visible.
- `<marker>` can include its own `location` coordinates to pinpoint bullet/number placement.
- Lists can nest; place the nested `list` inside a `list_item` of the parent list.
- When broken across pages, close items before the `page_break`, then re-open and continue with matching `thread` ids after the break.

### Forms

Fundamentally, forms are complex list with special list-items. This is why we introduced several new semantic items in the token-space,

| Token | Description |
|-------|-------------|
| `<form_item>` | Form item (with 1 key and 1 or more values as children) |
| `<form_header>` | Form header: this is specifically for headers in the form. |
| `<form_text>` | Form text: this is specifically for text-blocks in the form |
| `<key>` | key of the form item: can only be a child of `form_item` |
| `<value>` | value of the form item: can only be a child of `form_item`  |
| `<form>` | Form structure |

Notice that if we have captions or footnotes for the form, we will always start with the group of type form. Next, we can start with the form.

```xml
<group>
   <form>
      ... # (nested list of form, form_items, etc)
   </form>
</group>
```

If no caption/footnotes are present, one can skip the group of type form. In order to represent the hierarchy, we use the concept of nested forms. The children of a form item are supposed to be on the same level and the form-headers will be in reading-order, i.e. the form-items following the form-header will belong to that form header (similarly to items following the section-headers).

One peculiarity with the `<form_item>` is that it can have only 1 `<key>` as a child, but potentially one or more children of the type of `<value>` and `<checkbox>`

#### Form Examples

<details><summary><strong>Example 1</strong></summary><table><tr><td><textarea readonly rows="16" cols="40" style="resize: none; border: none; background: #f8f8f8; font-family: monospace;">
<form>
    <form_item>
        <key>Firma:</key>
        <value>Holcim ... GmbH</value>
    </form_item>
    <form_item>
        <key>Werk:</key>
        <value>Scholkholz</value>
    </form_item>
    ...
    <form_item>
        <key>Petrograph. Typ:</key>
        <value>Quartiarer Sand + Kies</value>
    </form_item>
</form>
</textarea></td><td>
<img src="examples/form/form_00.png" alt="form-00" width="100%">
</td></tr></table></details>

<details><summary><strong>Example 2</strong></summary><table><tr><td><textarea readonly rows="39" cols="40" style="resize: none; border: none; background: #f8f8f8; font-family: monospace;">
<form>
    <form_header>
        <marker>14.</marker>
        Transport Information
    </form_header>
    <form>
        <form_header>
            Land transport ... (Germany)
        </form_header>
        <form_item>
            <key>GGVS/GGVE class:</key>
            <value>8</value>
        </form_item>
        <form_item>
            <key>ADR/RID class:</key>
            <value>8</value>
        </form_item>
        ...
    </form>
    <form_item>
        <key>River transport ADN/ADNR</key>
        <value>not examined</value>
    </form_item>
    <form>
        <form_header>
            Sea transport IMDG
        </form_header>
        ...
    </form>
    ...
    <form_text>
        The transport ... considered.
    </form_text>
    <form_text>
        THESE TRANSPORT ... PACK!
    </form_text>
</form>
</textarea></td><td>
<img src="examples/form/form_01.png" alt="form-00" width="100%">
</td></tr></table></details>

<details><summary><strong>Example 3</strong></summary><table><tr><td><textarea readonly rows="39" cols="40" style="resize: none; border: none; background: #f8f8f8; font-family: monospace;">
<form>
    <form_item>
        <key>Description</key>
        <value>A.A. Cat</value>
    </form_item>
    <form_item>
        <key>Quant.</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Un</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Measure</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Price (in currency)</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Un</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Total</key>
        <value></value>
    </form_item>
    <form_text></form_text>
    <form>
        <form_item>
            <key>Delivery Cost</key>
            <value></value>
        </form_item>
        <form_item>
            <key>Maintenance</key>
            <value></value>
        </form_item>
        ...
    <form>
    <form>
        <form_item>
            <key>Date and time of delivery:</key>
            <value></value>
        </form_item>
        ...
        <form_item>
            <key>Guarantee</key>
            <value></value>
        </form_item>
        <form_text>
            Delivery Supplies ... Finance Department
        </form_text>
    </form>
    ...
</form>
</textarea></td><td>
<img src="examples/form/form_02.png" alt="form-00" width="100%">
</td></tr></table></details>

<details><summary><strong>Example 4</strong></summary><table><tr><td><textarea readonly rows="39" cols="40" style="resize: none; border: none; background: #f8f8f8; font-family: monospace;">
<form>
    <form_header>Information about you</form_header>
    <form_item>
        <key>
            \*Family Name (Last Name)
        </key>
        <value>staar</value>
    </form_item>
    <form_item>
        <key>\*Given Name (First Name)</key>
        <value>peter</value>
    </form_item>
    <form_item>
        <key>\*Middle Name (if applicable)</key>
        <value>WJ</value>
    </form_item>
    <form_item>
        <key>I am in the United States as a:</key>
        <checkbox selected="false">Visitor</checkbox>
        <checkbox selected="false">Student</checkbox>
        <checkbox selected="false">Permanent Resident</checkbox>
        <checkbox selected="false">Other (Specify)</checkbox>
        <form_text></form_text>
    <form_item>
    <form_item>
        <key>Country of Citizenship</key>
        <value></value>
    </form_item>
    <form_item>
        <key>\*Date of Birth</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Alien Registration Number (A-Number) (if any)</key>
        <value></value>
    </form_item>
    <form_header>Information About Your Address</form_header>
    <form_text>\*Present Physical Address ()No Po Boxes</form_text>
    <form_item>
        <key>\*Street ... Name</key>
        <value></value>
    </form_item>
    <form_item>
        <key>Apt.</key>
        <checkbox selected="false"></checkbox>
    </form_item>
    <form_item>
        <key>Ste.</key>
        <checkbox selected="false"></checkbox>
    </form_item>
    ...

</form>
</textarea></td><td>
<img src="examples/form/form_03.png" alt="form-00" width="100%">
</td></tr></table></details>

<details><summary><strong>Example 5</strong></summary><table><tr><td><textarea readonly rows="39" cols="40" style="resize: none; border: none; background: #f8f8f8; font-family: monospace;">
<form>
</form>
</textarea></td><td>
<img src="examples/form/form_04.png" alt="form-00" width="100%">
</td></tr></table></details>

<details><summary><strong>Example 6</strong></summary><table><tr><td><textarea readonly rows="39" cols="40" style="resize: none; border: none; background: #f8f8f8; font-family: monospace;">
<form>
</form>
</textarea></td><td>
<img src="examples/form/form_05.png" alt="form-00" width="100%">
</td></tr></table></details>

Example 7 has a classical duality between tables and explicit key-values,

<details><summary><strong>Example 7</strong></summary><table><tr><td><textarea readonly rows="39" cols="40" style="resize: none; border: none; background: #f8f8f8; font-family: monospace;">
<form>
    <form_item>
        <key>Adjusted CVSS v3.1 Score</key>
        <value>10.0</value>
    </form_item>
    <form_item>
        <key>Vector</key>
        <value>AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:L/A:H</value>
    </form_item>
    <form_item>
        <key>Likelihood</key>
        <value>Very High</value>
    </form_item>
    <form_item>
        <key>Impact</key>
        <value>Catastrophic</value>
    </form_item>
    <form_header>
      Affected Systems
    </form_header>
    <otsl>
    <ched/>IP Address<ched/>Port<ched/>Service<ched/>Version<nl/>
    <fcell/>10.0.0.101<fcell/>80/tcp, 8088/tcp<fcell/>Werkzeug<fcell/>3.0.1<nl/>
    <fcell/>10.0.0.102<fcell/>80/tcp, 8088/tcp<fcell/>Werkzeug<fcell/>3.0.1<nl/>
    <fcell/>10.0.0.103<fcell/>80/tcp, 8088/tcp<fcell/>Werkzeug<fcell/>3.0.1<nl/>
    </otsl>
</form>
</textarea></td><td>
<img src="examples/form/form_06.png" alt="form-00" width="100%">
</td></tr></table></details>

### Cross-page structure

We can capture content that is split across pages using the `<thread id="N"/>` token, where `N` is a unique identifier.

The basic structure is shown below, e.g. for a `text` tag:

```xml
<text>
  <thread id="1"/>
  This text item starts here
</text>
...
<page_break/>
...
<text>
  <thread id="1"/>
  and continues here.
</text>
```

Detailed examples: [link](./examples/cross_page/index.md)

### Formatting

Formatting may be preserved through nested tags or escape sequences:

- Bold, italic, underline, strikethrough
- Superscript, subscript
- Text direction markers

#### Page Break with Continuation

Page breaks are complex components that interrupt the flow of a document. They can interrupt paragraphs, tables, lists, etc. In general, we follow two rules,

1. If content spans across one (or more) page breaks, add `<thread id="N"/>` to the item and reuse the same `id` in the continuing item.
2. For the follow up content of the page, we follow a reading order and close all open tokens before the `<page_break/>` token is introduced.

An easy example is below,

```xml
<doctag>
  <text><thread id="1"/>This paragraph spans across</text>
  <caption>Some caption</caption>
  <page_break/>
  <text><thread id="1"/>multiple pages.</text>
</doctag>
```

Often, we have more complicated page breaks, in which a (nested) list is split across pages and further interrupted by other semantic elements (think page footers). In this case, we demand that all elements of the first page are added and/or closed **before** the page break and then opened again in the appropriate way after the page break, with the intent that the content in between the page breaks is a valid DocTags tree.

A more complicated example is shown below in which we break the content of a list-item,

```xml
<doctag>
  <list ordered=true>
    <thread id="1"/>
    <list_item>First item</list_item>
    <list_item><thread id="2"/>Second </list_item>
    ...
  </list>
  <page_footer>...</page_footer>
  <page_break/>
  <list ordered=true>
    <thread id="1"/>
    <list_item><thread id="2"/>item</list_item>
  </list>
  ...
</doctag>
```

Above, `<thread id="1"/>` captures that the list itself is split, while `<thread id="2"/>` captures that a particular
list item is split.

For tables that are broken across pages, we need to introduce two differnt tokens, namely the `<continue_col id=.../>` and `<continue_row id="..."/>`. Same principle applies, if the OTSL starts/ends with any of these tokens, we know the the tables needs to be merged.

## Implementation Requirements

### Parser Requirements

A conforming DocTags parser SHALL:

1. **Syntax Validation**: Recognize all tokens defined in this standard
2. **Geometric Processing**: Handle coordinate and bounding box elements correctly
3. **Version Support**: Process version information and apply appropriate parsing rules
4. **Hierarchy Validation**: Enforce parent-child relationship rules
5. **Continuation Handling**: Correctly link continued content across page breaks
6. **Error Reporting**: Provide meaningful error messages for invalid documents

### Serializer Requirements

A conforming DocTags serializer SHALL:

1. **Valid Output**: Generate syntactically correct DocTags documents
2. **Coordinate Normalization**: Ensure coordinates fit within specified resolution
3. **Structure Preservation**: Maintain element hierarchy and relationships
4. **Version Specification**: Include appropriate version information
5. **Continuation Integrity**: Ensure continuation tokens are properly paired

### Validation Rules

#### Required Structure Validation

- Root element must be `<doctag>`
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
- Coexistence: When both spatial and temporal tokens are present, both appear before content; relative order has no semantic effect.
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

| # | Category | Token | Self-Closing [Yes/No] | Parametrized [Yes,No] | Description |
|---|----------|-------|-----------------------|-----------------------|-------------|
| 1 | Root Elements | `doctag` | No | Yes | Root container; optional `version` attribute. |
| 2 | Special Elements | `page_break` | Yes | No | Page delimiter. |
| 3 |  | `time_break` | Yes | No | Temporal segment delimiter. |
| 4 |  | `metadata` | No | No | Document metadata container. |
| 5 | Geometric Tokens | `location` | Yes | Yes | Spatial coordinate; attributes: `value`, optional `resolution`. |
| 6 | Temporal Tokens | `hour` | Yes | Yes | Hours component of a timestamp; attribute: `value` in [0, 99]. |
| 7 |  | `minute` | Yes | Yes | Minutes component of a timestamp; attribute: `value` in [0, 59]. |
| 8 |  | `second` | Yes | Yes | Seconds component of a timestamp; attribute: `value` in [0, 59]. |
| 9 |  | `centisecond` | Yes | Yes | Centiseconds component of a timestamp; attribute: `value` in [0, 99]. |
| 10 | Semantic Tokens | `heading` | No | Yes | Section header; attribute: `level` (N ≥ 1). |
| 11 |  | `text` | No | No | Generic text content. |
| 12 |  | `caption` | No | No | Caption for floating/grouped elements. |
| 13 |  | `footnote` | No | No | Footnote content. |
| 14 |  | `page_header` | No | No | Page header content. |
| 15 |  | `page_footer` | No | No | Page footer content. |
| 16 |  | `watermark` | No | No | Watermark indicator or content. |
| 17 |  | `picture` | No | No | Image/graphic; may contain `base64` or `uri`. |
| 18 |  | `form` | No | No | Form structure container. |
| 19 |  | `formula` | No | No | Mathematical expression block. |
| 20 |  | `code` | No | No | Code block; may include classification via `class` token. |
| 21 |  | `list_item` | No | No | List item content. |
| 22 |  | `checkbox` | No | Yes | Checkbox item; attribute: `selected`. |
| 23 | Grouping Tokens | `section` | No | Yes | Document section; attribute: `level` (N ≥ 1). |
| 24 |  | `list` | No | Yes | List container; attribute: `ordered` (true/false). |
| 25 |  | `group` | No | Yes | Generic group. |
| 26 | Formatting Tokens | `bold` | No | No | Bold text. |
| 27 |  | `italic` | No | No | Italic text. |
| 28 |  | `strikethrough` | No | No | Strike-through text. |
| 29 |  | `superscript` | No | No | Superscript text. |
| 30 |  | `subscript` | No | No | Subscript text. |
| 31 |  | `rtl` | No | No | Right-to-left text direction. |
| 32 |  | `inline_formula` | No | No | Inline formula. |
| 33 |  | `inline_code` | No | No | Inline code. |
| 34 |  | `inline_picture` | No | No | Inline image/graphic. |
| 35 |  | `br` | Yes | No | Line break. |
| 36 | Structural Tokens (OTSL) | `otsl` | No | No | Table structure container. |
| 37 |  | `fcel` | Yes | No | New cell with content. |
| 38 |  | `ecel` | Yes | No | New cell without content. |
| 39 |  | `ched` | Yes | No | Column header cell. |
| 40 |  | `rhed` | Yes | No | Row header cell. |
| 41 |  | `corn` | Yes | No | Corner header cell. |
| 42 |  | `srow` | Yes | No | Section row separator cell. |
| 43 |  | `lcel` | Yes | No | Merge with left neighbor (horizontal span). |
| 44 |  | `ucel` | Yes | No | Merge with upper neighbor (vertical span). |
| 45 |  | `xcel` | Yes | No | Merge with left and upper neighbors (2D span). |
| 46 |  | `nl` | Yes | No | New line (row separator). |
| 47 | Continuation Tokens | `thread` | Yes | Yes | Continuation marker. |
| 48 |  | `h_thread` | Yes | Yes | Continutation marker for horizontal table stitching. |
| 49 | Binary Data Tokens | `base64` | No | No | Embedded binary data (base64). |
| 50 |  | `uri` | No | No | External resource reference. |
| 51 | Content Tokens | `marker` | No | No | List/form marker content. |
| 52 |  | `facets` | No | No | Container for application-specific properties for derived information, such as summary, classification label, etc. |
| 53 | Structural Tokens (Form) | `key` | No | No | Form item key (child of `form_item`). |
| 54 |  | `implicit_key` | No | No | Implicit key in forms. |
| 55 |  | `value` | No | No | Form item value (child of `form_item`). |

### Metadata Sub-elements

| # | Token | Self-Closing [Yes/No] | Parametrized [Yes,No] | Description |
|---|-------|-----------------------|-----------------------|-------------|
| 1 | `version` | No | No | Document version string (semantic versioning). |
| 2 | `title` | No | No | Document title (metadata context). |
| 3 | `author` | No | No | Author entry; may contain `affiliation` children and text. |
| 4 | `affiliation` | No | No | Author affiliation; child of `author`. |
| 5 | `date` | No | No | Document date in ISO 8601 format (e.g., YYYY-MM-DD). |
| 6 | `language` | No | Yes | Language code (ISO 639-3); attributes: `classifier`, `score`. |
| 7 | `default_resolution` | Yes | Yes | Default coordinate resolution; attributes: `width`, `height`. |
| 8 | `page_size` | Yes | Yes | Original page size; attributes: `width`, `height`. The optional `page_no` attribute start counting at 1. |
| 9 | `document_quality` | No | Yes | Quality score; attribute: `classifier`; content is a number [0,1]. |
| 10 | `document_readability` | No | Yes | Readability score; attribute: `classifier`; content is a number [0,1]. |
| 11 | `general_topic` | No | Yes | Topic label; attributes: `topic_taxonomy`, `classifier`, `score`. |
| 12 | `document_hash` | No | Yes | Document hash value; attribute: `hash_function` (e.g., SHA-256). |
| 13 | `custom_attribute` | No | Yes | Custom key/value; attributes: `key`, `name`; content is value. |
| 14 | `processing_tool` | No | No | Name of the processing tool (e.g., docling). |

## Appendix B: Escape entities

TBA
