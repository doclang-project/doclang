### Special Elements

This category comprises elements with specialized document-level function.

#### `<doclang>`

The document root element. Starts with an optional [`<head>`](#head) followed by a sequence of applicable elements.

##### Allowed context

Exists exactly once, as root element.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `xmlns` | Optional; default: "https://www.doclang.ai/ns/v1" | {"https://www.doclang.ai/ns/v1"} | The DocLang specification version namespace. |
| `version` | Optional; default: "1.0.0" | In format "x.y.z" as per Semantic Versioning | The DocLang specification version the document was produced against. |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Not allowed | Not allowed |

##### Example

```xml
<doclang xmlns="https://www.doclang.ai/ns/v1">
  <!-- content -->
</doclang>
```

#### `<head>`

Includes doc-level metadata.

##### Allowed context

Can only be first child of [`<doclang>`](#doclang).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Not allowed | Not allowed |

#### `<page_break>`

Indicates a page break. A paginated document may be divided into pages using the `<page_break/>` empty element. Any page content, as split by `<page_break/>`, forms a valid DocLang [document body](#head-and-body-areas), i.e. would be a valid DocLang document if wrapped in a `doclang` root element.

##### Allowed context

Can only be child of [`<doclang>`](#doclang).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

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

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<title>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<heading>`

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<caption>`

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<footnote>`

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<page_header>`

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<page_footer>`

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<field_region>`

Serves for scoping of field items, for example encapsulating a whole form.

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Not allowed | Allowed |

#### `<otsl>`

Captures a table using OTSL format. A table cell, as delimited  by the respective structural elements, can be defined either by normal semantic / grouping elements or by an optional component head followed by raw or formatted text, which is to be interpreted as an "implicit [`<text>`](#text)" (i.e. without the wrapping tags).

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<list>`

##### Allowed context

Any context that allows semantic elements.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `class` | Optional; default: "unordered" | {"unordered", "ordered"} |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Not allowed | Allowed |

#### `<formula>`

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Not allowed |

#### `<code>`

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Not allowed |

#### `<picture>`

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Not allowed | Allowed |

#### `<marker>`

##### Allowed context

Any context that allows semantic elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<list_text>`

##### Allowed context

Can only be child of [`<list>`](#list).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<field_heading>`

##### Allowed context

Can only be descendant of [`<field_region>`](#field_region).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<field_item>`

Scoping of a field key (optional) & any corresponding values.

##### Allowed context

Can only be descendant of [`<field_region>`](#field_region).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Not allowed | Allowed |

#### `<key>`

The key of a field (may correspond to  0-N field values).

##### Allowed context

Can only be descendant of [`<field_item>`](#field_item).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<value>`

A value of a field (may correspond to 0 or 1 field key).

##### Allowed context

Can only be descendant of [`<field_item>`](#field_item).

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `class` | Optional; default: "read_only" | {"read_only", "fillable"} |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

#### `<hint>`

A hint regarding a field.

##### Allowed context

Can only be descendant of [`<field_region>`](#field_region).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Allowed | Allowed |

### Grouping Elements

Grouping elements enable the encapsulation of semantic elements or other grouping elements. Any grouping element may optionally begin with a [component head](#component-head-elements).

#### `<group>`

[TODO: revise] Generic container to be used for grouping mixed-type components.

##### Allowed context

Any context that allows grouping elements.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Not allowed | Allowed |

#### `<floating_group>`

[TODO: revise] Container that groups a floating component with its caption, footnotes etc.

##### Allowed context

Any context that allows grouping elements.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `class` | Required | {"table", "picture", "code", "formula"} |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Allowed | Not allowed | Allowed |

### Component Head Elements

The component head is a sequence comprising the following elements in this order, whereby all elements are optional:<br /><ul><li>`<thread>`</li><li>`<h_thread>`</li><li>`<meta>`</li><li>sequence of 2*N `<location>`s (N>1)</li><li>sequence of `<timestamp>`s</li><li>`<layer>`</li></ul> A component head can only appear as the leading content of a semantic or grouping element, or also of `<otsl>` in the context of "implicit `<text>`s".<br/> The various component head elements are further specified in the following subsections.

#### `<thread>`

Optional part of the component head; serves for capturing a component spanning multiple bounding boxes (e.g. cross-column) or pages.<br/>  To capture such a component, we define separate instances of the respective element and use a [`<thread>`](#thread) with the same `thread_id` attribute for all of them.

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `thread_id` | Required | Postive integer | A string that identifies a thread. |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

##### Example

<details>
  <summary>Show document picture</summary>

  <img src="../input/examples/thread.png" width="700">

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

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `h_thread_id` | Required | Postive integer |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<meta>`

Used to store additional or derived information regarding the respective component.

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Not allowed | Not allowed |

#### `<custom_meta>`

Custom metadata, e.g. for application-specific purposes.

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Not allowed | Not allowed |

#### `<location>`

Coordinate system is the bottom-left corner of the page.

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `value` | Required | Integer within [0, resolution) |  |
| `resolution` | Optional; defaults to head metadata [`<default_resolution>`](#default_resolution), otherwise "512" | Postive integer |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<timestamp>`

needed? Yes, if the individual hour/minute/etc are not all required (else cannot unambiguously interpret `<hour>0</hour><minute>2</minute><second>3</second>`)

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Not allowed | Not allowed |

#### `<hour>`

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `value` | Required | Non-negative integer |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<minute>`

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `value` | Required | Non-negative integer |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<second>`

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `value` | Required | Non-negative integer |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<centisecond>`

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `value` | Required | Non-negative integer |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<layer>`

##### Allowed context

Can only be child of a semantic or a grouping element (or of [`<otsl>`](#otsl) in the context of "implicit [`<text>`](#text)s").

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `class` | Optional; default: "body" | {"body", "furniture", "background", "invisible", "notes"} |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<summary>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<classification>`

##### Allowed context

Can only be child of [`<meta>`](#meta).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Not allowed |

### Payload Elements

Payload elements are low-level elements that help define the effective content of another element.

#### `<uri>`

Textual content must be a URI.

##### Allowed context

Can only be child of [`<picture>`](#picture) or first child of [`<hyperlink>`](#hyperlink).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Not allowed |

#### `<checkbox>`

##### Allowed context

Any context that allows raw text content.

##### Attributes

| Attribute | Required / Optional | Allowed Values | Description |
|-----------|----------|----------------|-------------|
| `selected` | Optional;default: "false" | {"false", "true"} |  |

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<content>`

##### Allowed context

Any context that allows raw text content.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Not allowed |

### Formatting Elements

Formatting elements modify the styling and presentation within semantic or other formatting elements.

#### `<bold>`

##### Allowed context

Any context that allows raw text content.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Allowed |

#### `<italic>`

##### Allowed context

Any context that allows raw text content.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Allowed |

#### `<underline>`

##### Allowed context

Any context that allows raw text content.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Allowed |

#### `<strikethrough>`

##### Allowed context

Any context that allows raw text content.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Allowed |

#### `<superscript>`

##### Allowed context

Any context that allows raw text content.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Allowed |

#### `<subscript>`

##### Allowed context

Any context that allows raw text content.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Allowed |

#### `<handwriting>`

##### Allowed context

Any context that allows raw text content.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Allowed |

#### `<rtl>`

Indicates right-to-left direction.

##### Allowed context

Any context that allows raw text content.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Allowed |

#### `<hyperlink>`

Contains a [`<uri>`](#uri) and then optionally raw or formatted text data.

##### Allowed context

Any context that allows raw text content.

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Allowed | Not allowed | Allowed | Allowed |

### Structural Elements

Structural elements define boundaries within tabular content (`<otsl>`).

#### `<fcel>`

##### Allowed context

Can only be child of [`<otsl>`](#otsl).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<ecel>`

##### Allowed context

Can only be child of [`<otsl>`](#otsl).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<ched>`

##### Allowed context

Can only be child of [`<otsl>`](#otsl).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<rhed>`

##### Allowed context

Can only be child of [`<otsl>`](#otsl).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<corn>`

##### Allowed context

Can only be child of [`<otsl>`](#otsl).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<srow>`

##### Allowed context

Can only be child of [`<otsl>`](#otsl).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<lcel>`

##### Allowed context

Can only be child of [`<otsl>`](#otsl).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<ucel>`

##### Allowed context

Can only be child of [`<otsl>`](#otsl).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<xcel>`

##### Allowed context

Can only be child of [`<otsl>`](#otsl).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

#### `<nl>`

##### Allowed context

Can only be child of [`<otsl>`](#otsl).

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| Not allowed | Not allowed | Not allowed | Not allowed |

### Document Head Elements

This category comprises the document-level metadata elements that are the building blocks of `<head>`.

#### `<title>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<author>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<date>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<default_resolution>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<page_size>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<language>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<generated_by>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<topic>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<summary>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<document_hash>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<licenses>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<data_classification>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<acceptable_use>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<stewardship>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<access_policy>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<retention_policy>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

#### `<compliance_requirements>`

TBD

##### Allowed context

TBD

##### Attributes

None

##### Content Types

| XML content | Component head | Raw text | Semantic / grouping elements |
| --- | --- | --- | --- |
| TBD | TBD | TBD | TBD |

