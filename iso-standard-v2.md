# ISO XXX - DocTags: Universal Document Markup Format (Revised)

## Foreword

This document was prepared by Peter Staar, Maroun touma, Panos Vagenas and (FILL IN!). This International Standard specifies the DocTags format, a universal markup language for representing structured document content with semantic, spatial, and formatting information.

## Introduction

The proliferation of digital documents across diverse formats (PDF, HTML, Word, etc.) has created significant challenges in document processing, conversion, and understanding. Current approaches often result in loss of semantic information, structural relationships, or spatial context during document conversion.

DocTags addresses these challenges by providing a minimalist, unambiguous markup format that:
- Preserves complete document structure and semantics
- Maintains spatial and layout information when appropriate
- Supports complex document elements including tables, formulas, code, nested lists, and charts
- Enables lossless round-trip conversion between formats regarding content

This standard builds upon research in document understanding and is intended to represent the content of a document as accurately as possible while maintaining implementation simplicity.

## Scope

This International Standard specifies:
- The syntax and semantics of the DocTags markup language
- Rules for encoding document structure, content, and metadata
- Mechanisms for representing spatial layout and pagination
- Methods for preserving formatting and text direction
- Specifications for complex document elements (tables, charts, formulas, code, forms)
- Requirements for conforming implementations

## DocTags Structure

### Relationship to XML

DocTags is a constrained subset of XML with the following characteristics:
- Simplified syntax with a finite set of allowed tags
- Constrained use of attributes on most elements
- Character-based encoding using legal Unicode characters (except Null)
- Standard XML parsing rules apply for markup vs content distinction

### Document Definition and Versioning

Every DocTags document is wrapped in a root `<doctag>` element with optional version specification:

```xml
<doctag version="1.0.0">
  <!-- document content -->
</doctag>
```

Version numbering follows Semantic Versioning (MAJOR.MINOR.PATCH). When no version is specified, the default is v1.0.0.

### Metadata and Document Structure

Optional metadata can be included using the `<metadata>` element:

```xml
<doctag version="1.2.3">
  <metadata>
    <version>1.2.3</version>
    <title>Document Title</title>
    <author>
	Author Name
	<affiliation></affiliation>
    </author>
    <date>2024-01-01</date>
    <language>en</language>
    <default_resolution width="512" height="512"/>
  </metadata>
  <body>
    <!-- document content -->
  </body>
</doctag>
```

The keys `version`, `title`, `abstract`, `author`, `affiliation`, `date`, `reference`, `language` and `default_resolution` are protected.

Documents may be divided into pages using the self-closing `<page_break/>` element,

```xml
<doctag>
  <!-- page 1 content -->
  <page_break/>
  <!-- page 2 content -->
</doctag>
```

## Token Vocabulary

DocTags defines seven categories of tokens: **semantic**, **spatial**, **grouping**, **structural**, **content**, **formatting**, and **continuation** tokens.

### Semantic Tokens

These tokens represent the semantic intent of document content:

| Token | Description | Content Type |
|-------|-------------|--------------|
| `<title>` | Document or section title | text |
| `<section_header level="N">` | Section header (N ≥ 1) | text |
| `<text>` | Generic text content | text |
| `<caption>` | Caption for floating elements | text |
| `<footnote>` | Footnote content | text |
| `<page_header>` | Page header content | text |
| `<page_footer>` | Page footer content | text |
| `<list_item>` | List item | text |
| `<document_index>` | Table of contents or index | structural |
| `<formula>` | Mathematical expression | structural |
| `<code>` | Code block | structural |
| `<table>` | Table structure | structural |
| `<picture>` | Image or graphic element | structural |
| `<form>` | Form structure | structural |



### Grouping Tokens

These tokens organize semantic content into logical structures:

| Token | Description | Allowed Children |
|-------|-------------|------------------|
| `<section level="N">` | Document section (N ≥ 1) | semantic, grouping |
| `<group>` | Generic grouping | semantic, grouping |
| `<inline>` | Inline text grouping | semantic (text-type only) |
| `<ordered_list>` | Numbered list | list_item, checkbox_* |
| `<unordered_list>` | Bulleted list | list_item, checkbox_* |

### List Item Tokens

Special semantic tokens for list structures:

| Token | Description | Parent Elements |
|-------|-------------|-----------------|
| `<list_item>` | List item content | ordered_list, unordered_list |
| `<checkbox_selected>` | Selected checkbox item | ordered_list, unordered_list |
| `<checkbox_unselected>` | Unselected checkbox item | ordered_list, unordered_list |

### Spatial Tokens

Spatial information uses a set of location elements with value (and optional resolution) attributes of the format `<loc value="integer" resolution="integer">` with 0<=value<=resolution.

- Single coordinate at (100, 200): `<loc value="100"/><loc value="200"/>`
- Bounding box with (x0, y0) = (100, 200) and (x1, y1) = (300, 400): `<loc value="100"/><loc value="200"/>`<loc value="300"/>`<loc value="400"/>`

If no resolution is provided, coordinates are normalized to the document's default resolution from the `metadata` (default: 512×512).

### Structural Tokens

#### Table Structure (OTSL - Optimized Table Structure Language)

Tabular structure and header semantics in DocTags represented by optimized table-structure language (OTSL) tokens.
Each new cell OTSL token (`<fcel/>` with it's semantic variants) is interleaved by the sequence of approptiate table cell content tokens (texts, lists, etc.).
OTSL representation has minimized vocabulary and specific rules.
The benefits of describing tables with OTSL in reducing number of structural tokens (5 essential in OTSL vs 28+ in HTML) and shorten structural sequence length to half of HTML representation on average.
Structural tokens define the structure of a table: columns, rows, cells, merged cells. Each cell can then be specified with semantic vatiant token if it's: column-header, row-header, section row separator, or corner-header.
Semantic variants of `<fcel/>` token are following the same rules as `<fcel/>` token, and used just to distinguish a function of a table cell: type of header or separator.

| Token | Semantic variant | Description |
|-------|---------|-------------|
| `<otsl>` | - | start of table data structure |
| `<fcel/>`| `<fcel/>` | a new cell |
|          | `<ched/>`| a new column header cell |
|          | `<rhed/>`| a new row header cell |
|          | `<corn/>`| a new corner header cell |
|          | `<srow/>`| a new section row cell |
| `<lcel/>`| - | left-looking cell, merging with the left neighbor cell to create a horizontal span |
| `<ucel/>`| - | up-looking cell, merging structure with the upper neighbor cell to create a vertical span |
| `<xcel/>`| - | cross cell to merge with both left and upper neighbor cells, for 2D spans |
| `<nl/>`| - | new line, table row separator |

OTSL enables easy error detection and correction during sequence generation, making it LLM friendly.
A notable attribute of OTSL is that it has the capability of achieving lossless conversion to HTML.

The OTSL representation follows these syntax rules:

- Left-looking cell rule: The left neighbour of an `<lcel/>` must be either another `<lcel/>` or one of the variants of `<fcel/>`.
- Up-looking cell rule: The upper neighbour of a `<ucel/>` must be either another `<ucel/>` or one of the variants of `<fcel/>`.
- Cross cell rule: The left neighbour of an `<xcel/>` cell must be either another `<xcel/>` or a `<ucel/>`, and the upper neighbour of an `<xcel/>` must be either another `<xcel/>` or an `<lcel/>`.
- First row rule: Only `<lcel/>` and `<fcel/>`(with variants) are allowed in the first row.
- First column rule: Only `<ucel/>` cells and `<fcel/>`(with variants) are allowed in the first column.
- Rectangular rule: The table representation of structural OTSL tokens is always rectangular - all rows must have an equal number of OTSL tokens, terminated with `<nl/>` token.


#### Form Structure

| Token | Description |
|-------|-------------|
| `<key>` | Form field label |
| `<implicit_key>` | Implied field label |
| `<value>` | Form field value |

### Content Tokens

| Token | Description |
|-------|-------------|
| `<content>` | Explicit content wrapper: this wrapper is mostly optional but can be useful for the case os escaping. |
| `<summary>` | This token allows to provide a short summary of the content. |
| `<marker>` | List marker (e.g., "i", "ii", "•") |
| `<class>` | Classification (language, chart type, etc.) |

### Formatting Tokens

| Token | Description |
|-------|-------------|
| `<bold>` | Bold text |
| `<italic>` | Italic text |
| `<strikethrough>` | Struck-through text |
| `<superscript>` | Superscript |
| `<subscript>` | Subscript |
| `<rtl>` | Right-to-left text direction |

### Continuation Tokens

For content spanning page breaks:

| Token | Description |
|-------|-------------|
| `<thread_N/>` | Content continues (N is unique identifier) |
| `<continue_row id="N"/>` | Content continues row-wise for the table (N is unique identifier), only used in OTSL |
| `<continue_col id="N"/>` | Content continues column-wise (N is unique identifier), only used in OTSL |

### Attributes Tokens

Documents can have attributes:

| Token | Description |
|-------|-------------|
| `<language_identification id="N"/>` | Identify language such as english, german, french, spanish, japanese, etc. |
| `<document_quality classifier="C" class="N" score="S"/>` | Content quality assessment using standard algorithms such as DCLM, gneissweb, etc. |
| `<document_readability score="R"/>` | Indicates how easy a a document can be undertood by a general audiance |
| `<general_topic topic="T"/>` | topic that the document is most likely to fall in such as Science and Technology, Legal, etc. |


## Grammar and Structure Rules

### Hierarchical Nesting Rules

1. **Text-type semantic elements** (title, section_header, text, caption, etc.) may only contain:
   - Content tokens
   - Formatting tokens
   - Inline grouping
   - Other text-type semantic elements

2. **Structural-type semantic elements** (table, picture, form, etc.) may contain:
   - Caption, footnote
   - Structural tokens
   - Spatial tokens
   - Content tokens

3. **List structures** follow strict parent-child relationships:
   - `<ordered_list>` and `<unordered_list>` may only contain list item tokens
   - List item tokens may only appear within list groupings

### Document Examples

#### Simple Document Structure

In the simplest document example, document elements are in a flat list,

```xml
<doctag version="1.0.0">
  <title>Research Paper Title</title>
  <section_header level="1">Abstract</section_header>
  <text>This paper presents...</text>
  <section_header level="1">Introduction</section_header>
  <text>In recent years...</text>
  <section_header level="2">Background</section_header>
  <text>Previous work has shown...</text>
</doctag>
```

The user is allowed to add sections or groups as he sees fit, but it is not a strong requirement,

```xml
<doctag version="1.0.0">
  <title>Research Paper Title</title>

  <section level="1">
    <section_header level="1">Abstract</section_header>
    <text>This paper presents...</text>
  </section>

  <section level="1">
    <section_header level="1">Introduction</section_header>
    <text>In recent years...</text>

    <section level="2">
      <section_header level="2">Background</section_header>
      <text>Previous work has shown...</text>
    </section>
  </section>
</doctag>
```

In case of page-layout information, the coordinates are provided at the semantic element level,

```xml
<doctag version="1.0.0">
  <title>
    <loc value="10"/><loc value="20"/><loc value="30"/><loc value="40"/>
    Research Paper Title
  </title>

  <section level="1">
    <section_header level="1">
      <loc value="10"/><loc value="20"/><loc value="30"/><loc value="40"/>
      Abstract
    </section_header>
    <text>
      <loc value="10"/><loc value="20"/><loc value="30"/><loc value="40"/>
      This paper presents...
    </text>
  </section>

  <section level="1">
    <section_header level="1">Introduction</section_header>
    <text>In recent years...</text>

    <section level="2">
      <section_header level="2">Background</section_header>
      <text>Previous work has shown...</text>
    </section>
  </section>
</doctag>
```

#### Table Example

```xml
<table>
  <bbox x0="100" y0="50" x1="400" y1="200"/>
  <caption>
    <bbox x0="100" y0="20" x1="400" y1="45"/>
    Table 1: Experimental Results
  </caption>
  <otsl>
    <bbox x0="100" y0="50" x1="400" y1="150"/>
    <ched/>Method<ched/>Accuracy<nl/>
    <fcel/>Baseline<fcel/>0.85<nl/>
    <fcel/>Proposed<fcel/>0.92<nl/>
  </otsl>
</table>
```

#### List Example

```xml
<unordered_list>
  <list_item>
    <marker>•</marker>
    First item with <bold>bold</bold> text
  </list_item>
  <list_item>
    <marker>•</marker>
    Second item
  </list_item>
  <checkbox_selected>Completed task</checkbox_selected>
  <checkbox_unselected>Pending task</checkbox_unselected>
</unordered_list>
```

### Form

```xml
<form><loc_50/><loc_100/><loc_450/><loc_200/>
  <unordered_list>
    <list_item><loc_50/><loc_100/><loc_200/><loc_130/>
      <key>Name:</key>
      <value>John</value>
    </list_item>
    <list_item><loc_50/><loc_100/><loc_200/><loc_130/>
      <blind_key></blind_key>
      <value>19 Dec 2020</value>
    </list_item>
    <checked_box>Male
    </checked_box>
    <unchecked_box>Female
    </unchecked_box>
    ...
  </unordered_list>
</form>
```

Extensive list of examples: [link](./form-examples/form-examples.md)

### Cross-page structure

We can capture content that is split across pages using the `thread_N` token, where `N` is a unique identifier.

The basic structure is shown below, e.g. for a `text` tag:

```xml
<text>
  <thread_1/>
  This text item starts here
</text>
...
<page_break/>
...
<text>
  <thread_1/>
  and continues here.
</text>
```

Detailed examples: [link](./examples/cross_page/index.md)

### Inline structure

The inline structure allows the document to have complex representation of text. Children of the inline group are not required to have location tokens.

```xml
<inline><loc_50/><loc_100/><loc_200/><loc_130/>
  <text>The superconducting transition temperature</text>
  <formula>T^c</formula>
  ...
</inline>
```

For any complex notation in text items (including section-headers, list-items, text items, captions etc). Notice that inline groups can also be used to capture flowing text across columns, eg

```xml
<text>
  <inline><loc_50/><loc_100/><loc_100/><loc_130/>
    <text>The superconducting transition temperature</text>
    <formula>T^c</formula>
    ...
  </inline>
  <inline><loc_110/><loc_100/><loc_200/><loc_130/>
    ...
  </inline>
</text>
```

### Split tables

Detailed examples: [link](./examples/split_tables/index.md)


### Formatting

Formatting may be preserved through nested tags or escape sequences:

- Bold, italic, underline, strikethrough
- Superscript, subscript
- Text direction markers


#### Page Break with Continuation

Page breaks are complex components that interupt the flow of a document. They can interupt paragraphs, tables, lists, etc. In general, we follow two rules,

1. If we have content that jumps over one (or more) page-breaks, we append the `<continue_N>` token to the item. The same token is then used in the beginning of the item that continues the content.
2. For the follow up content of the page, we follow a reading order and close all open tokens before the `<page_break/>` token is introduced.

An easy example is below,

```xml
<doctag>
  <text><thread_1/>This paragraph spans across</text>
  <caption>Some caption</caption>
  <page_break/>
  <text><thread_1/>multiple pages.</text>
</doctag>
```

Often, we have more complicated page breaks, in which a (nested) list is split across pages and further interupted by other semantic elements (think page-footers). In this case, we demand that all elements of the first page are added and/or closed __before__ the page break and then opened again in the appropriate way after the page break, with the intent that the content in between the page breaks is valid Doctags tree.

A more complicated example is shown below in which we break the content of a list-item,

```xml
<doctag>
  <ordered_list>
    <thread_1/>
    <list_item>First item</list_item>
    <list_item><thread_2/>Second </list_item>
    ...
  </ordered_list>
  <page_footer>...</page_footer>
  <page_break/>
  <ordered_list>
    <thread_1/>
    <list_item><thread_2/>item</list_item>
  </ordered_list>
  ...
</doctag>
```

Above, `thread_1` captures the fact that the list itself is split, while `thread_2` captures the fact that a particular
list item is split.

For tables that are broken across pages, we need to introduce two differnt tokens, namely the `<continue_col id=.../>` and `<continue_row id="..."/>`. Same principle applies, if the OTSL starts/ends with any of these tokens, we know the the tables needs to be merged.

## Implementation Requirements

### Parser Requirements

A conforming DocTags parser SHALL:

1. **Syntax Validation**: Recognize all tokens defined in this standard
2. **Spatial Processing**: Handle coordinate and bounding box elements correctly
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

#### Spatial Validation

- Coordinates must be within [0, resolution] bounds
- Bounding boxes must satisfy x0 ≤ x1 and y0 ≤ y1
- Spatial elements should appear in reading order when possible

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
7. Semantic Versioning 2.0.0 (semver.org)

## Appendix A: Complete Token Reference

### Token Hierarchy

```
DocTags Tokens
├── Root Elements
│   └── <doctag version="X.Y.Z">
├── Semantic Tokens
│   ├── Text Type: title, section_header, text, caption, footnote, page_header, page_footer
│   ├── Structural Type: table, picture, form, formula, code, document_index
│   └── List Type: list_item, checkbox_selected, checkbox_unselected
├── Grouping Tokens
│   ├── section, group, inline
│   └── ordered_list, unordered_list
├── Spatial Tokens
│   ├── <coord x="N" y="N"/>
│   └── <bbox x0="N" y0="N" x1="N" y1="N"/>
├── Structural Tokens
│   ├── OTSL: otsl, fcel, ecel, lcel, ucel, xcel, nl, ched, rhed
│   └── Form: key, implicit_key, value
├── Content Tokens
│   ├── content, marker, class
│   └── <thread_N/>
├── Formatting Tokens
│   └── bold, italic, strikethrough, superscript, subscript, rtl
└── Special Elements
    ├── <page_break/>
    ├── <metadata>
    └── <body>
```

This revised standard addresses the major inconsistencies while maintaining the core vision of DocTags as a universal document markup format.
