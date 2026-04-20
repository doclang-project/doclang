### Special Elements

This category comprises elements with specialized document-level function.

#### `<doclang>`

The document root element. Starts with an optional [`<head>`](#head) followed by a sequence of applicable elements.

##### Allowed Context

Exists exactly once, as root element.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `xmlns` | Optional; default: "https://www.doclang.ai/ns/v1" | {"https://www.doclang.ai/ns/v1"} | The DocLang specification version namespace. |
| `version` | Optional; default: "1.0.0" | In format "x.y.z" as per Semantic Versioning | The DocLang specification version the document was produced against. |

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Not allowed | Not allowed |

##### Example

```xml
<doclang xmlns="https://www.doclang.ai/ns/v1">
  <!-- content -->
</doclang>
```

#### `<head>`

Includes doc-level metadata.

##### Allowed Context

Can only be first child of [`<doclang>`](#doclang).

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Not allowed | Not allowed |

#### `<page_break>`

Indicates a page break. A paginated document may be divided into pages using the `<page_break/>` empty element. Any page content, as split by `<page_break/>`, forms a valid DocLang [document body](#head-and-body-areas), i.e. would be a valid DocLang document if wrapped in a `doclang` root element.

##### Allowed Context

Can only be child of [`<doclang>`](#doclang).

##### Attributes

None

##### Allowed Content Types

None (empty element).

##### Example

```xml
<doclang xmlns="https://www.doclang.ai/ns/v1">
  <!-- first page content -->
  <page_break/>
  <!-- second page content -->
</doclang>
```

### Semantic Elements

Semantic elements capture core components with specific meaning and functional role in the document, for example, a paragraph, a table, a list, and more. Any semantic element may optionally begin with a [component head](#component-head-elements). Semantic elements are generally meant to be interpreted as block-level elements (although they can also be inlined via nesting).

#### `<text>`

Represents a piece of cohesive text as that would appear in a paragraph.

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

#### `<heading>`

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

#### `<caption>`

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

#### `<footnote>`

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

#### `<page_header>`

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

#### `<page_footer>`

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

#### `<field_region>`

Serves for scoping of field items, for example encapsulating a whole form.

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Not allowed | Allowed |

#### `<table>`

Captures a table based on the OTSL format. Table cells are delimited by the respective structural elements.

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Not allowed | Allowed |

#### `<list>`

Captures a list. List items are delimited by the respective structural elements.

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `class` | Optional; default: "unordered" | {"unordered", "ordered"} |  |

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Not allowed | Allowed |

#### `<formula>`

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Not allowed |

#### `<code>`

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Not allowed |

#### `<picture>`

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Not allowed | Allowed |

#### `<marker>`

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

#### `<group>`

Container for encapsulating multiple semantic elements.

##### Allowed Context

Any context that allows semantic elements.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Not allowed | Allowed |

#### `<field_heading>`

##### Allowed Context

Can only be descendant of [`<field_region>`](#field_region).

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

#### `<field_item>`

Scoping of a field key (optional) and any corresponding values.

##### Allowed Context

Can only be descendant of [`<field_region>`](#field_region).

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Not allowed | Allowed |

#### `<key>`

The key of a field (may correspond to  0-N field values).

##### Allowed Context

Can only be descendant of [`<field_item>`](#field_item).

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

#### `<value>`

A value of a field (may correspond to 0 or 1 field key).

##### Allowed Context

Can only be descendant of [`<field_item>`](#field_item).

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `class` | Optional; default: "read_only" | {"read_only", "fillable"} |  |

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

#### `<hint>`

A hint regarding a field.

##### Allowed Context

Can only be descendant of [`<field_region>`](#field_region).

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Allowed | Allowed | Allowed |

### Component Head Elements

The component head is a sequence comprising the following elements in this order, whereby all elements are optional:<br /><ul><li>`<thread>`</li><li>`<h_thread>`</li><li>`<meta>`</li><li>sequence of 2*N `<location>`s (N>1)</li><li>sequence of `<timestamp>`s</li><li>`<layer>`</li></ul> A component head can only appear as the leading content of a semantic or grouping element, or also of `<otsl>` in the context of "implicit `<text>`s".<br/> The various component head elements are further specified in the following subsections.

#### `<thread>`

Optional part of the component head; serves for capturing a component spanning multiple bounding boxes (e.g. cross-column) or pages.<br/>  To capture such a component, we define separate instances of the respective element and use a [`<thread>`](#thread) with the same `thread_id` attribute for all of them.

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `thread_id` | Required | Postive integer | A string that identifies a thread. |

##### Allowed Content Types

None (empty element).

##### Example

<details>
  <summary>Show document picture</summary>

  <img src="reference/input/examples/thread.png" width="700">

</details>

```xml
<doclang xmlns="https://www.doclang.ai/ns/v1">
  <!-- ... -->
  <text>
    <thread thread_id="1"/>
    <location value="10"/><location value="20"/>
    <location value="30"/><location value="40"/>
    where τ<subscript>x,y,z</subscript> are the Pauli matrices acting
    on Nambu space. We consider a circular-shaped boundary, the nor-
  </text>

  <caption>
    <location value="20"/><location value="30"/>
    <location value="40"/><location value="50"/>
    FIG. 3. The modules of the inner product of two MES spinors
    <formula><!-- ... --></formula>
    <!-- ... -->
  </caption>

  <text>
    <thread thread_id="1"/>
    <location value="30"/><location value="40"/>
    <location value="50"/><location value="60"/>
    mal direction of the boundary tangent for arbitrary angle θ is
    <formula><!-- ... --></formula>
    <!-- ... -->
  </text>
</doclang>
```

#### `<h_thread>`

Optional part of the component head; serves for capturing a component crossing horizontal boundaries (e.g. table verically split between multiple pages).

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `h_thread_id` | Required | Postive integer |  |

##### Allowed Content Types

None (empty element).

#### `<meta>`

Used to store additional or derived information regarding the respective component.

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Not allowed | Not allowed |

#### `<custom_meta>`

Custom metadata, e.g. for application-specific purposes.

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Not allowed | Not allowed |

#### `<location>`

Coordinate system is the bottom-left corner of the page.

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `value` | Required | Integer within [0, resolution) |  |
| `resolution` | Optional; defaults to head metadata [`<default_resolution>`](#default_resolution), otherwise "512" | Postive integer |  |

##### Allowed Content Types

None (empty element).

#### `<timestamp>`

TBD. Needed, if the individual hour/minute/etc are not all required (else cannot unambiguously interpret `<hour>0</hour><minute>2</minute><second>3</second>`)

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Not allowed | Not allowed |

#### `<hour>`

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `value` | Required | Non-negative integer |  |

##### Allowed Content Types

None (empty element).

#### `<minute>`

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `value` | Required | Non-negative integer |  |

##### Allowed Content Types

None (empty element).

#### `<second>`

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `value` | Required | Non-negative integer |  |

##### Allowed Content Types

None (empty element).

#### `<centisecond>`

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `value` | Required | Non-negative integer |  |

##### Allowed Content Types

None (empty element).

#### `<layer>`

##### Allowed Context

Can only be child of a semantic element.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `class` | Optional; default: "body" | {"body", "furniture", "background", "invisible", "notes"} |  |

##### Allowed Content Types

None (empty element).

#### `<summary>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<classification>`

##### Allowed Context

Can only be child of [`<meta>`](#meta).

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

### Payload Elements

Payload elements are low-level elements that help define the effective content of another element.

#### `<uri>`

Textual content must be a URI.

##### Allowed Context

Can only be child of [`<picture>`](#picture) or first child of [`<hyperlink>`](#hyperlink).

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

#### `<checkbox>`

##### Allowed Context

Any context that allows raw text content.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `selected` | Optional;default: "false" | {"false", "true"} |  |

##### Allowed Content Types

None (empty element).

#### `<content>`

##### Allowed Context

Any context that allows raw text content.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

### Formatting Elements

Formatting elements modify the styling and presentation within semantic or other formatting elements.

#### `<bold>`

##### Allowed Context

Any context that allows raw text content.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

#### `<italic>`

##### Allowed Context

Any context that allows raw text content.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

#### `<underline>`

##### Allowed Context

Any context that allows raw text content.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

#### `<strikethrough>`

##### Allowed Context

Any context that allows raw text content.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

#### `<superscript>`

##### Allowed Context

Any context that allows raw text content.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

#### `<subscript>`

##### Allowed Context

Any context that allows raw text content.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

#### `<handwriting>`

##### Allowed Context

Any context that allows raw text content.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

#### `<rtl>`

Indicates right-to-left direction.

##### Allowed Context

Any context that allows raw text content.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

#### `<hyperlink>`

Contains a [`<uri>`](#uri) and then optionally raw or formatted text data.

##### Allowed Context

Any context that allows raw text content.

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Allowed | Not allowed |

### Structural Elements

Structural elements define boundaries within tabular content (`<otsl>`).

#### `<fcel>`

##### Allowed Context

Can only be child of [`<table>`](#table).

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<ecel>`

##### Allowed Context

Can only be child of [`<table>`](#table).

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<ched>`

##### Allowed Context

Can only be child of [`<table>`](#table).

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<rhed>`

##### Allowed Context

Can only be child of [`<table>`](#table).

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<corn>`

##### Allowed Context

Can only be child of [`<table>`](#table).

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<srow>`

##### Allowed Context

Can only be child of [`<table>`](#table).

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<lcel>`

##### Allowed Context

Can only be child of [`<table>`](#table).

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<ucel>`

##### Allowed Context

Can only be child of [`<table>`](#table).

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<xcel>`

##### Allowed Context

Can only be child of [`<table>`](#table).

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<nl>`

##### Allowed Context

Can only be child of [`<table>`](#table).

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<ldiv>`

Delimiter defining the beginning of a list item. It can either be empty or contain a [`<marker>`](#marker).

##### Allowed Context

Can only be child of [`<list>`](#list).

##### Attributes

None

##### Allowed Content Types

| Component head | Raw text | Semantic elements |
| --- | --- | --- |
| Not allowed | Not allowed | Only [`<marker>`](#marker) |

### Document Head Elements

This category comprises the document-level metadata elements that are the building blocks of `<head>`.

#### `<title>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<author>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<date>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<default_resolution>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<page_size>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<language>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<generated_by>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<topic>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<summary>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<document_hash>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<licenses>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<data_classification>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<acceptable_use>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<stewardship>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<access_policy>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<retention_policy>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

#### `<compliance_requirements>`

TBD

##### Allowed Context

TBD

##### Attributes

None

##### Allowed Content Types

None (empty element).

