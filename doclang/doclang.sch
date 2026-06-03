<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron"
            xmlns:dl="https://www.doclang.ai/ns/v0"
            queryBinding="xslt3">

  <sch:title>Doclang Schematron Validation Rules (XSLT 3.0)</sch:title>

  <sch:ns prefix="dl" uri="https://www.doclang.ai/ns/v0"/>

  <!-- ============================================ -->
  <!-- NOTE: Element head order is enforced by XSD element_head group -->
  <!-- Schematron only validates structural tokens (ldiv for lists, cell tokens for tables) -->
  <!-- ============================================ -->

  <!-- ============================================ -->
  <!-- LIST: Must start with ldiv (after optional element head) -->
  <!-- ============================================ -->

  <sch:pattern id="list-structure">
    <sch:rule context="dl:list[*]">
      <sch:let name="first-non-header" value="*[not(self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:custom)][1]"/>

      <sch:assert test="not($first-non-header) or $first-non-header[self::dl:ldiv]">
        List must have ldiv as first element after optional element head (property elements: label, thread, xref, href, layer, location, caption, custom).
        Found: <sch:value-of select="if ($first-non-header) then name($first-non-header) else 'nothing'"/>
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TABLE: Must start with cell token (after optional element head) -->
  <!-- ============================================ -->

  <sch:pattern id="table-structure">
    <sch:rule context="dl:table[*] | dl:index[*]">
      <sch:let name="first-non-header" value="*[not(self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:custom)][1]"/>

      <sch:assert test="not($first-non-header) or
                        $first-non-header[self::dl:fcel or self::dl:ecel or self::dl:ched or
                                         self::dl:rhed or self::dl:corn or self::dl:srow or
                                         self::dl:lcel or self::dl:ucel or self::dl:xcel]">
        Table and index must have cell-starting token as first element after optional element head (property elements: label, thread, xref, href, layer, location, caption, custom).
        Found: <sch:value-of select="if ($first-non-header) then name($first-non-header) else 'nothing'"/>
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TABLE: Rectangular grid validation -->
  <!-- Ensures all rows have the same number of columns -->
  <!-- ============================================ -->

  <sch:pattern id="table-rectangular-grid">
    <sch:rule context="dl:table[dl:nl] | dl:index[dl:nl]">
      <!-- Define cell-starting tokens (tokens that begin a new cell) -->
      <sch:let name="cell-tokens" value="dl:fcel | dl:ecel | dl:ched | dl:rhed | dl:corn | dl:srow | dl:lcel | dl:ucel | dl:xcel"/>

      <!-- Count cells in first row (before first nl) -->
      <sch:let name="first-row-cells" value="count($cell-tokens[following-sibling::dl:nl[1] is current()/dl:nl[1]])"/>

      <!-- Check that all subsequent rows have the same number of cells -->
      <sch:assert test="every $nl in dl:nl[position() > 1] satisfies
                        count($cell-tokens[preceding-sibling::dl:nl[1] is $nl/preceding-sibling::dl:nl[1] and
                                          following-sibling::dl:nl[1] is $nl]) = $first-row-cells">
        Table and index must follow the rectangular rule: all rows must have the same number of cells.
        First row has <sch:value-of select="$first-row-cells"/> cells, but at least one other row has a different count.
        Each row should have the same count of cell-starting tokens (fcel, ecel, ched, rhed, corn, srow, lcel, ucel, xcel) before each nl element.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- ELEMENT HEAD: Text must not precede property elements -->
  <!-- Property elements: label, thread, xref, href, layer, location, caption, custom (per XSD element_head group) -->
  <!-- This rule applies to regular semantic elements AND virtual <text> in lists/tables -->
  <!-- ============================================ -->

  <sch:pattern id="element-head-placement">
    <sch:rule context="dl:text | dl:heading | dl:code | dl:formula | dl:caption |
                       dl:page_header | dl:page_footer | dl:footnote | dl:picture | dl:marker |
                       dl:field_region | dl:field_heading | dl:field_item | dl:key | dl:value |
                       dl:list | dl:table | dl:index | dl:group">
      <sch:let name="header-elements" value="dl:label | dl:thread | dl:xref | dl:href | dl:layer | dl:location | dl:caption | dl:custom"/>

      <sch:let name="text-before-header" value="text()[following-sibling::*[self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:custom]]"/>

      <sch:assert test="every $t in $text-before-header satisfies normalize-space($t) = ''">
        Property elements in the element head (label, thread, xref, href, layer, location, caption, custom) must appear before any non-whitespace text content.
        Found non-whitespace text before element head: '<sch:value-of select="normalize-space(string-join($text-before-header, ''))"/>'
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- ELEMENT HEAD: xref and href are mutually exclusive -->
  <!-- ============================================ -->

  <sch:pattern id="xref-href-mutual-exclusivity">
    <sch:rule context="*[dl:xref and dl:href]">
      <sch:assert test="false()">
        Element head must not contain both xref and href elements; they are mutually exclusive.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- XREF: referenced thread_id must be defined by at least one thread element -->
  <!-- ============================================ -->

  <sch:pattern id="xref-thread-defined">
    <sch:rule context="dl:xref">
      <sch:assert test="exists(//dl:thread[@thread_id = current()/@thread_id])">
        Element xref references thread_id="<sch:value-of select="@thread_id"/>" but no thread element defines that id.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- LOCATION: value must be within [0, axis_limit) -->
  <!-- axis_limit precedence: location@resolution, head/default_resolution axis, fallback 512 -->
  <!-- ============================================ -->

  <sch:pattern id="location-value-range">
    <sch:rule context="dl:location">
      <sch:let name="location-index" value="count(preceding-sibling::dl:location) + 1"/>
      <sch:let name="is-x-axis" value="$location-index mod 2 = 1"/>
      <sch:let name="doc-default-width" value="if (/dl:doclang/dl:head[1]/dl:default_resolution[1]/@width)
                                               then number(/dl:doclang/dl:head[1]/dl:default_resolution[1]/@width)
                                               else 512"/>
      <sch:let name="doc-default-height" value="if (/dl:doclang/dl:head[1]/dl:default_resolution[1]/@height)
                                                then number(/dl:doclang/dl:head[1]/dl:default_resolution[1]/@height)
                                                else 512"/>
      <sch:let name="axis-limit" value="if (@resolution)
                                       then number(@resolution)
                                       else if ($is-x-axis)
                                       then $doc-default-width
                                       else $doc-default-height"/>

      <sch:assert test="number(@value) ge 0 and number(@value) lt $axis-limit">
        Location value must satisfy 0 &lt;= value &lt; axis_limit.
        Found value=<sch:value-of select="@value"/>, axis_limit=<sch:value-of select="$axis-limit"/>,
        axis=<sch:value-of select="if ($is-x-axis) then 'x' else 'y'"/>,
        location-index=<sch:value-of select="$location-index"/>.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- LOCATION BLOCK: enforce x0<=x1 and y0<=y1 -->
  <!-- ============================================ -->

  <sch:pattern id="location-block-order">
    <sch:rule context="*[dl:location]">
      <sch:let name="x0" value="number(dl:location[1]/@value)"/>
      <sch:let name="y0" value="number(dl:location[2]/@value)"/>
      <sch:let name="x1" value="number(dl:location[3]/@value)"/>
      <sch:let name="y1" value="number(dl:location[4]/@value)"/>

      <!-- Effective resolution for each coordinate -->
      <sch:let name="doc-default-width" value="if (/dl:doclang/dl:head[1]/dl:default_resolution[1]/@width)
                                               then number(/dl:doclang/dl:head[1]/dl:default_resolution[1]/@width)
                                               else 512"/>
      <sch:let name="doc-default-height" value="if (/dl:doclang/dl:head[1]/dl:default_resolution[1]/@height)
                                                then number(/dl:doclang/dl:head[1]/dl:default_resolution[1]/@height)
                                                else 512"/>

      <sch:let name="x0-res" value="if (dl:location[1]/@resolution)
                                     then number(dl:location[1]/@resolution)
                                     else $doc-default-width"/>
      <sch:let name="y0-res" value="if (dl:location[2]/@resolution)
                                     then number(dl:location[2]/@resolution)
                                     else $doc-default-height"/>
      <sch:let name="x1-res" value="if (dl:location[3]/@resolution)
                                     then number(dl:location[3]/@resolution)
                                     else $doc-default-width"/>
      <sch:let name="y1-res" value="if (dl:location[4]/@resolution)
                                     then number(dl:location[4]/@resolution)
                                     else $doc-default-height"/>

      <sch:let name="x0-norm" value="$x0 div $x0-res"/>
      <sch:let name="y0-norm" value="$y0 div $y0-res"/>
      <sch:let name="x1-norm" value="$x1 div $x1-res"/>
      <sch:let name="y1-norm" value="$y1 div $y1-res"/>

      <sch:assert test="$x0-norm le $x1-norm and $y0-norm le $y1-norm">
        Location block must satisfy x0_norm &lt;= x1_norm and y0_norm &lt;= y1_norm,
        where *_norm is each coordinate normalized by its effective resolution.
        Found:
        x0=<sch:value-of select="$x0"/>, x0_res=<sch:value-of select="$x0-res"/>, x0_norm=<sch:value-of select="$x0-norm"/>,
        x1=<sch:value-of select="$x1"/>, x1_res=<sch:value-of select="$x1-res"/>, x1_norm=<sch:value-of select="$x1-norm"/>,
        y0=<sch:value-of select="$y0"/>, y0_res=<sch:value-of select="$y0-res"/>, y0_norm=<sch:value-of select="$y0-norm"/>,
        y1=<sch:value-of select="$y1"/>, y1_res=<sch:value-of select="$y1-res"/>, y1_norm=<sch:value-of select="$y1-norm"/>.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- THREAD: same thread_id must not span different host element types -->
  <!-- Host type is the parent semantic element (list, list-item, table, table-cell, text, picture, etc.) -->
  <!-- ============================================ -->

  <sch:pattern id="thread-host-type-consistency">
    <sch:rule context="dl:doclang">
      <sch:let name="threads" value="//dl:thread"/>
      <sch:let name="thread-ids" value="distinct-values($threads/@thread_id)"/>
      <sch:let name="cell-token-names" value="('fcel','ecel','ched','rhed','corn','srow','lcel','ucel','xcel')"/>
      <sch:assert test="every $tid in $thread-ids satisfies
                        count(distinct-values(
                          for $t in $threads[@thread_id = $tid]
                          return
                            if ($t/parent::dl:list) then
                              (if ($t/preceding-sibling::dl:ldiv) then 'list-item' else 'list')
                            else if ($t/parent::dl:table or $t/parent::dl:index) then
                              (if ($t/preceding-sibling::*[local-name() = $cell-token-names]) then 'table-cell' else local-name($t/parent::*))
                            else local-name($t/parent::*)
                        )) = 1">
        All thread elements with the same thread_id must use the same host element type
        (e.g. all text, not text and picture). Check thread_id values for mixed types.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- VIRTUAL TEXT IN LISTS: Element head must precede content -->
  <!-- A list item (content between <ldiv> siblings) acts as a virtual <text> -->
  <!-- and must follow the same element head rules -->
  <!-- ============================================ -->

  <sch:pattern id="list-virtual-text-element-head">
    <sch:rule context="dl:list/dl:ldiv">
      <sch:let name="next-ldiv" value="following-sibling::dl:ldiv[1]"/>

      <sch:let name="item-content" value="if ($next-ldiv)
                                          then following-sibling::node()[following-sibling::dl:ldiv[1] is $next-ldiv]
                                          else following-sibling::node()"/>

      <sch:let name="header-elements" value="$item-content[self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:custom]"/>

      <sch:let name="first-header-index" value="if ($header-elements)
                                                 then index-of($item-content, $header-elements[1])[1]
                                                 else 0"/>

      <sch:let name="text-before-header" value="if ($first-header-index > 0)
                                                 then for $i in 1 to ($first-header-index - 1)
                                                      return $item-content[$i][self::text()][normalize-space(.) != '']
                                                 else ()"/>

      <sch:assert test="empty($text-before-header)">
        In list items (virtual text), property elements in the element head (label, thread, xref, href, layer, location, caption, custom) must appear before any non-whitespace text content.
        Found non-whitespace text before element head: '<sch:value-of select="normalize-space(string-join($text-before-header, ''))"/>'
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- VIRTUAL TEXT IN TABLES: Element head must precede content -->
  <!-- A table cell (content after cell-starting tokens) acts as a virtual <text> -->
  <!-- and must follow the same element head rules -->
  <!-- ============================================ -->

  <sch:pattern id="table-virtual-text-element-head">
    <sch:rule context="dl:table/dl:fcel | dl:table/dl:ecel | dl:table/dl:ched |
                       dl:table/dl:rhed | dl:table/dl:corn | dl:table/dl:srow |
                       dl:table/dl:lcel | dl:table/dl:ucel | dl:table/dl:xcel |
                       dl:index/dl:fcel | dl:index/dl:ecel | dl:index/dl:ched |
                       dl:index/dl:rhed | dl:index/dl:corn | dl:index/dl:srow |
                       dl:index/dl:lcel | dl:index/dl:ucel | dl:index/dl:xcel">
      <sch:let name="next-token" value="following-sibling::*[self::dl:fcel or self::dl:ecel or self::dl:ched or
                                                              self::dl:rhed or self::dl:corn or self::dl:srow or
                                                              self::dl:lcel or self::dl:ucel or self::dl:xcel or
                                                              self::dl:nl][1]"/>

      <sch:let name="cell-content" value="if ($next-token)
                                          then following-sibling::node()[following-sibling::*[. is $next-token]]
                                          else following-sibling::node()[not(following-sibling::dl:nl)]"/>

      <sch:let name="header-elements" value="$cell-content[self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:custom]"/>

      <sch:let name="first-header-index" value="if ($header-elements)
                                                 then index-of($cell-content, $header-elements[1])[1]
                                                 else 0"/>

      <sch:let name="text-before-header" value="if ($first-header-index > 0)
                                                 then for $i in 1 to ($first-header-index - 1)
                                                      return $cell-content[$i][self::text()][normalize-space(.) != '']
                                                 else ()"/>

      <sch:assert test="empty($text-before-header)">
        In table and index cells (virtual text), property elements in the element head (label, thread, xref, href, layer, location, caption, custom) must appear before any non-whitespace text content.
        Found non-whitespace text before element head: '<sch:value-of select="normalize-space(string-join($text-before-header, ''))"/>'
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- FIELD STRUCTURE: placement and key cardinality -->
  <!-- Enforces Appendix A field ancestry constraints -->
  <!-- ============================================ -->
  <sch:pattern id="field-structure-placement">
    <sch:rule context="dl:field_heading">
      <sch:assert test="exists(ancestor::dl:field_region)">
        field_heading and field_item must be descendants of field_region.
      </sch:assert>
    </sch:rule>

    <sch:rule context="dl:field_item">
      <sch:assert test="exists(ancestor::dl:field_region)">
        field_heading and field_item must be descendants of field_region.
      </sch:assert>
    </sch:rule>

    <sch:rule context="dl:key">
      <sch:assert test="exists(ancestor::dl:field_item)">
        key and value must be descendants of field_item.
      </sch:assert>
    </sch:rule>

    <sch:rule context="dl:value">
      <sch:assert test="exists(ancestor::dl:field_item)">
        key and value must be descendants of field_item.
      </sch:assert>
    </sch:rule>

    <sch:rule context="dl:field_item">
      <sch:let name="own-key-count" value="count(.//dl:key[count(ancestor::dl:field_item) = 1])"/>
      <sch:assert test="$own-key-count le 1">
        A field_item may contain at most one own descendant key.
        Keys that belong to nested field_item descendants are excluded from this count.
        Found own-key-count=<sch:value-of select="$own-key-count"/>.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- PICTURE BODY: table only as first body element when class="chart" -->
  <!-- ============================================ -->

  <sch:pattern id="picture-body">
    <sch:rule context="dl:picture">
      <sch:let name="first-body" value="*[not(self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:custom)][1]"/>

      <sch:assert test="not(not(@class) or @class = 'undefined') or empty(dl:table)">
        Picture with class="undefined" (or no class) must not contain table in the element body.
      </sch:assert>

      <sch:assert test="empty(dl:table) or (@class = 'chart' and dl:table[1] is $first-body)">
        Element table is only allowed as the first element of the body of picture with class="chart".
      </sch:assert>
    </sch:rule>
  </sch:pattern>

</sch:schema>
