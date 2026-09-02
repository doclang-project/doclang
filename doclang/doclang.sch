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
      <sch:let name="first-non-header" value="*[not(self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:description or self::dl:summary or self::dl:custom)][1]"/>

      <sch:assert test="not($first-non-header) or $first-non-header[self::dl:ldiv]">
        List must have ldiv as first element after optional element head (property elements: label, thread, xref, href, layer, location, caption, description, summary, custom).
        Found: <sch:value-of select="if ($first-non-header) then name($first-non-header) else 'nothing'"/>
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TRACK: Must start with bdiv (after optional element head) -->
  <!-- ============================================ -->

  <sch:pattern id="track-structure">
    <sch:rule context="dl:track[*]">
      <sch:let name="first-non-header" value="*[not(self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:description or self::dl:summary or self::dl:custom)][1]"/>
      <sch:let name="text-before-first-bdiv" value="text()[following-sibling::dl:bdiv and not(preceding-sibling::dl:bdiv)][normalize-space(.) != '']"/>

      <sch:assert test="not($first-non-header) or $first-non-header[self::dl:bdiv]">
        Track must have bdiv as first element after optional element head (property elements: label, thread, xref, href, layer, location, caption, description, summary, custom).
        Found: <sch:value-of select="if ($first-non-header) then name($first-non-header) else 'nothing'"/>
      </sch:assert>

      <sch:assert test="empty($text-before-first-bdiv)">
        Track must not contain non-whitespace text before its first cue block (bdiv).
        Found: '<sch:value-of select="normalize-space(string-join($text-before-first-bdiv, ''))"/>'
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TABLE: Must start with cell token (after optional element head) -->
  <!-- ============================================ -->

  <sch:pattern id="table-structure">
    <sch:rule context="dl:table[*] | dl:index[*]">
      <sch:let name="first-non-header" value="*[not(self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:description or self::dl:summary or self::dl:custom)][1]"/>

      <sch:assert test="not($first-non-header) or
                        $first-non-header[self::dl:fcel or self::dl:ecel or self::dl:ched or
                                         self::dl:rhed or self::dl:corn or self::dl:srow or
                                         self::dl:lcel or self::dl:ucel or self::dl:xcel]">
        Table and index must have cell-starting token as first element after optional element head (property elements: label, thread, xref, href, layer, location, caption, description, summary, custom).
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
      <sch:let name="first-nl" value="dl:nl[1]"/>
      <sch:let name="first-row-cells" value="count($cell-tokens[following-sibling::dl:nl[1] is $first-nl])"/>

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
  <!-- Property elements: label, thread, xref, href, layer, location, caption, description, summary, custom (per XSD element_head group) -->
  <!-- This rule applies to regular semantic elements AND virtual <text> in lists/tables -->
  <!-- ============================================ -->

  <sch:pattern id="element-head-placement">
    <sch:rule context="dl:text | dl:heading | dl:code | dl:formula | dl:caption | dl:description | dl:summary |
                       dl:page_header | dl:page_footer | dl:footnote | dl:picture | dl:marker |
                       dl:field_region | dl:field_heading | dl:field_item | dl:key | dl:value |
                       dl:list | dl:table | dl:index | dl:group | dl:track | dl:voice | dl:chapter | dl:frame | dl:audio">
      <sch:let name="header-elements" value="dl:label | dl:thread | dl:xref | dl:href | dl:layer | dl:location | dl:caption | dl:description | dl:summary | dl:custom"/>

      <sch:let name="text-before-header" value="text()[following-sibling::*[self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:description or self::dl:summary or self::dl:custom]]"/>

      <sch:assert test="every $t in $text-before-header satisfies normalize-space($t) = ''">
        Property elements in the element head (label, thread, xref, href, layer, location, caption, description, summary, custom) must appear before any non-whitespace text content.
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
      <sch:let name="thread-id" value="@thread_id"/>
      <sch:assert test="exists(//dl:thread[@thread_id = $thread-id])">
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

      <sch:let name="header-elements" value="$item-content[self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:description or self::dl:summary or self::dl:custom]"/>

      <sch:let name="first-header-index" value="if ($header-elements)
                                                 then index-of($item-content, $header-elements[1])[1]
                                                 else 0"/>

      <sch:let name="text-before-header" value="if ($first-header-index > 0)
                                                 then for $i in 1 to ($first-header-index - 1)
                                                      return $item-content[$i][self::text()][normalize-space(.) != '']
                                                 else ()"/>

      <sch:assert test="empty($text-before-header)">
        In list items (virtual text), property elements in the element head (label, thread, xref, href, layer, location, caption, description, summary, custom) must appear before any non-whitespace text content.
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

      <sch:let name="header-elements" value="$cell-content[self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:description or self::dl:summary or self::dl:custom]"/>

      <sch:let name="first-header-index" value="if ($header-elements)
                                                 then index-of($cell-content, $header-elements[1])[1]
                                                 else 0"/>

      <sch:let name="text-before-header" value="if ($first-header-index > 0)
                                                 then for $i in 1 to ($first-header-index - 1)
                                                      return $cell-content[$i][self::text()][normalize-space(.) != '']
                                                 else ()"/>

      <sch:assert test="empty($text-before-header)">
        In table and index cells (virtual text), property elements in the element head (label, thread, xref, href, layer, location, caption, description, summary, custom) must appear before any non-whitespace text content.
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
  <!-- PICTURE BODY: src first when present; tabular only for chart, immediately after src -->
  <!-- ============================================ -->

  <sch:pattern id="picture-body">
    <sch:rule context="dl:picture">
      <sch:let name="first-body" value="*[not(self::dl:label or self::dl:thread or self::dl:xref or self::dl:href or self::dl:layer or self::dl:location or self::dl:caption or self::dl:description or self::dl:summary or self::dl:custom)][1]"/>

      <sch:assert test="empty(dl:tabular) or @class = 'chart'">
        Element tabular is only allowed in picture with class="chart".
      </sch:assert>

      <sch:assert test="empty(dl:src) or dl:src[1] is $first-body">
        Element src must be the first element of the picture body when present.
      </sch:assert>

      <sch:assert test="empty(dl:tabular) or (not(dl:src) and dl:tabular[1] is $first-body) or (dl:src and dl:tabular[1] is dl:src/following-sibling::*[1])">
        Element tabular must immediately follow src when src is present, otherwise it may be the first body element.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TRACK CUE BLOCK: must open with a start timestamp; no text before it -->
  <!-- The cue block is the run of siblings after a <bdiv/> up to the next <bdiv/> -->
  <!-- ============================================ -->

  <sch:pattern id="track-cue-block">
    <sch:rule context="dl:track/dl:bdiv">
      <sch:let name="next-bdiv" value="following-sibling::dl:bdiv[1]"/>
      <sch:let name="cue-content" value="if ($next-bdiv)
                                         then following-sibling::node()[following-sibling::dl:bdiv[1] is $next-bdiv]
                                         else following-sibling::node()"/>
      <sch:let name="first-elem" value="$cue-content[self::*][1]"/>
      <sch:let name="first-elem-index" value="if ($first-elem)
                                              then index-of($cue-content, $first-elem)[1]
                                              else 0"/>
      <sch:let name="text-before-first-elem" value="if ($first-elem-index > 0)
                                                    then for $i in 1 to ($first-elem-index - 1)
                                                         return $cue-content[$i][self::text()][normalize-space(.) != '']
                                                    else $cue-content[self::text()][normalize-space(.) != '']"/>

      <sch:assert test="not($first-elem) or $first-elem[self::dl:hours or self::dl:minutes]">
        A track cue block must begin with a start timestamp: its first element must be hours or minutes.
        Found: <sch:value-of select="if ($first-elem) then name($first-elem) else 'nothing'"/>
      </sch:assert>

      <sch:assert test="empty($text-before-first-elem)">
        A track cue block must not contain non-whitespace text before its start timestamp.
        Found: '<sch:value-of select="normalize-space(string-join($text-before-first-elem, ''))"/>'
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TRACK CUE BLOCK: end timestamp must not precede the start timestamp -->
  <!-- ============================================ -->

  <sch:pattern id="track-cue-block-timestamp-order">
    <sch:rule context="dl:track/dl:bdiv">
      <sch:let name="next-bdiv" value="following-sibling::dl:bdiv[1]"/>
      <sch:let name="cue" value="if ($next-bdiv)
                                 then following-sibling::*[following-sibling::dl:bdiv[1] is $next-bdiv]
                                 else following-sibling::*"/>
      <sch:let name="mins" value="$cue[self::dl:minutes]"/>

      <sch:let name="m1" value="$mins[1]"/>
      <sch:let name="h1" value="$m1/preceding-sibling::*[1][self::dl:hours]"/>
      <sch:let name="s1" value="$m1/following-sibling::dl:seconds[1]"/>
      <sch:let name="ms1" value="$s1/following-sibling::*[1][self::dl:msecs]"/>
      <sch:let name="start-ms" value="3600000 * (if ($h1) then number($h1/@value) else 0)
                                      + 60000 * number($m1/@value)
                                      + 1000 * number($s1/@value)
                                      + (if ($ms1) then number($ms1/@value) else 0)"/>

      <sch:let name="m2" value="$mins[2]"/>
      <sch:let name="h2" value="$m2/preceding-sibling::*[1][self::dl:hours]"/>
      <sch:let name="s2" value="$m2/following-sibling::dl:seconds[1]"/>
      <sch:let name="ms2" value="$s2/following-sibling::*[1][self::dl:msecs]"/>
      <sch:let name="end-ms" value="3600000 * (if ($h2) then number($h2/@value) else 0)
                                    + 60000 * number($m2/@value)
                                    + 1000 * number($s2/@value)
                                    + (if ($ms2) then number($ms2/@value) else 0)"/>

      <sch:assert test="count($mins) != 2 or $end-ms ge $start-ms">
        A track cue block end timestamp must not be earlier than its start timestamp.
        Found start=<sch:value-of select="$start-ms"/>ms, end=<sch:value-of select="$end-ms"/>ms.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TRACK CUE BLOCK: cue blocks appear in non-decreasing order of start time -->
  <!-- (blocks may still overlap, e.g. simultaneous speakers) -->
  <!-- ============================================ -->

  <sch:pattern id="track-cue-block-sequence">
    <sch:rule context="dl:track/dl:bdiv[preceding-sibling::dl:bdiv]">
      <sch:let name="prev-bdiv" value="preceding-sibling::dl:bdiv[1]"/>

      <sch:let name="m1" value="following-sibling::dl:minutes[1]"/>
      <sch:let name="h1" value="$m1/preceding-sibling::*[1][self::dl:hours]"/>
      <sch:let name="s1" value="$m1/following-sibling::dl:seconds[1]"/>
      <sch:let name="ms1" value="$s1/following-sibling::*[1][self::dl:msecs]"/>
      <sch:let name="start-ms" value="3600000 * (if ($h1) then number($h1/@value) else 0)
                                      + 60000 * number($m1/@value)
                                      + 1000 * number($s1/@value)
                                      + (if ($ms1) then number($ms1/@value) else 0)"/>

      <sch:let name="pm1" value="$prev-bdiv/following-sibling::dl:minutes[1]"/>
      <sch:let name="ph1" value="$pm1/preceding-sibling::*[1][self::dl:hours]"/>
      <sch:let name="ps1" value="$pm1/following-sibling::dl:seconds[1]"/>
      <sch:let name="pms1" value="$ps1/following-sibling::*[1][self::dl:msecs]"/>
      <sch:let name="prev-start-ms" value="3600000 * (if ($ph1) then number($ph1/@value) else 0)
                                           + 60000 * number($pm1/@value)
                                           + 1000 * number($ps1/@value)
                                           + (if ($pms1) then number($pms1/@value) else 0)"/>

      <sch:assert test="$start-ms ge $prev-start-ms">
        Track cue blocks must appear in non-decreasing order of start time.
        Found this cue block start=<sch:value-of select="$start-ms"/>ms, previous cue block start=<sch:value-of select="$prev-start-ms"/>ms.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TRACK CHAPTER: a <chapter> marks a boundary at its cue block's start time; -->
  <!-- consecutive chapter boundaries must be strictly increasing (no two chapters at one instant) -->
  <!-- ============================================ -->

  <sch:pattern id="track-chapter-strictly-increasing">
    <sch:rule context="dl:track/dl:chapter[preceding-sibling::dl:chapter]">
      <!-- start time of the cue block this <chapter> belongs to (first timestamp run after its <bdiv>) -->
      <sch:let name="m1" value="preceding-sibling::dl:bdiv[1]/following-sibling::dl:minutes[1]"/>
      <sch:let name="h1" value="$m1/preceding-sibling::*[1][self::dl:hours]"/>
      <sch:let name="s1" value="$m1/following-sibling::dl:seconds[1]"/>
      <sch:let name="ms1" value="$s1/following-sibling::*[1][self::dl:msecs]"/>
      <sch:let name="start-ms" value="3600000 * (if ($h1) then number($h1/@value) else 0)
                                      + 60000 * number($m1/@value)
                                      + 1000 * number($s1/@value)
                                      + (if ($ms1) then number($ms1/@value) else 0)"/>

      <sch:let name="pm1" value="preceding-sibling::dl:chapter[1]/preceding-sibling::dl:bdiv[1]/following-sibling::dl:minutes[1]"/>
      <sch:let name="ph1" value="$pm1/preceding-sibling::*[1][self::dl:hours]"/>
      <sch:let name="ps1" value="$pm1/following-sibling::dl:seconds[1]"/>
      <sch:let name="pms1" value="$ps1/following-sibling::*[1][self::dl:msecs]"/>
      <sch:let name="prev-start-ms" value="3600000 * (if ($ph1) then number($ph1/@value) else 0)
                                           + 60000 * number($pm1/@value)
                                           + 1000 * number($ps1/@value)
                                           + (if ($pms1) then number($pms1/@value) else 0)"/>

      <sch:assert test="$start-ms gt $prev-start-ms">
        Each chapter must begin strictly later than the previous chapter; two chapters cannot mark the same instant.
        Found this chapter start=<sch:value-of select="$start-ms"/>ms, previous chapter start=<sch:value-of select="$prev-start-ms"/>ms.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TRACK CUE BLOCK: an <audio> clip spans [start, end], so its cue block needs an end time -->
  <!-- ============================================ -->

  <sch:pattern id="track-audio-requires-end">
    <sch:rule context="dl:track/dl:bdiv">
      <sch:let name="next-bdiv" value="following-sibling::dl:bdiv[1]"/>
      <sch:let name="cue" value="if ($next-bdiv)
                                 then following-sibling::*[following-sibling::dl:bdiv[1] is $next-bdiv]
                                 else following-sibling::*"/>

      <sch:assert test="not($cue[self::dl:audio]) or count($cue[self::dl:minutes]) = 2">
        A track cue block with an audio clip must carry an end time; the clip spans the cue block's interval [start, end].
      </sch:assert>
    </sch:rule>
  </sch:pattern>

</sch:schema>
