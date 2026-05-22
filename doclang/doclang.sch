<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron"
            xmlns:dl="https://www.doclang.ai/ns/v0"
            queryBinding="xslt3">

  <sch:title>Doclang Schematron Validation Rules (XSLT 3.0)</sch:title>

  <sch:ns prefix="dl" uri="https://www.doclang.ai/ns/v0"/>

  <!-- ============================================ -->
  <!-- FLOATING_GROUP: Validate class-specific content -->
  <!-- ============================================ -->

  <sch:pattern id="floating-group-picture">
    <sch:rule context="dl:floating_group[@class='picture']">
      <sch:assert test="count(.//dl:picture) >= 1">
        A floating_group with class="picture" must contain at least one picture element.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <sch:pattern id="floating-group-table">
    <sch:rule context="dl:floating_group[@class='table']">
      <sch:assert test="count(.//dl:table) >= 1">
        A floating_group with class="table" must contain at least one table element.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <sch:pattern id="floating-group-code">
    <sch:rule context="dl:floating_group[@class='code']">
      <sch:assert test="count(.//dl:code) >= 1">
        A floating_group with class="code" must contain at least one code element.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- NOTE: Component header order (meta, location, layer) is enforced by XSD component_header group -->
  <!-- Schematron only validates structural tokens (ldiv for lists, cell tokens for tables) -->
  <!-- ============================================ -->

  <!-- ============================================ -->
  <!-- LIST: Must start with ldiv (after optional component_header) -->
  <!-- ============================================ -->

  <sch:pattern id="list-structure">
    <sch:rule context="dl:list[*]">
      <sch:let name="first-non-header" value="*[not(self::dl:xref or self::dl:href or self::dl:meta or self::dl:location or self::dl:layer)][1]"/>
      
      <sch:assert test="not($first-non-header) or $first-non-header[self::dl:ldiv]">
        List must have ldiv as first element after optional component header (xref, href, meta, location, layer).
        Found: <sch:value-of select="if ($first-non-header) then name($first-non-header) else 'nothing'"/>
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TABLE: Must start with cell token (after optional component_header) -->
  <!-- ============================================ -->

  <sch:pattern id="table-structure">
    <sch:rule context="dl:table[*]">
      <sch:let name="first-non-header" value="*[not(self::dl:xref or self::dl:href or self::dl:meta or self::dl:location or self::dl:layer)][1]"/>
      
      <sch:assert test="not($first-non-header) or
                        $first-non-header[self::dl:fcel or self::dl:ecel or self::dl:ched or
                                         self::dl:rhed or self::dl:corn or self::dl:srow or
                                         self::dl:lcel or self::dl:ucel or self::dl:xcel]">
        Table must have cell-starting token as first element after optional component header (xref, href, meta, location, layer).
        Found: <sch:value-of select="if ($first-non-header) then name($first-non-header) else 'nothing'"/>
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- TABLE: Rectangular grid validation -->
  <!-- Ensures all rows have the same number of columns -->
  <!-- ============================================ -->

  <sch:pattern id="table-rectangular-grid">
    <sch:rule context="dl:table[dl:nl]">
      <!-- Define cell-starting tokens (tokens that begin a new cell) -->
      <sch:let name="cell-tokens" value="dl:fcel | dl:ecel | dl:ched | dl:rhed | dl:corn | dl:srow | dl:lcel | dl:ucel | dl:xcel"/>
      
      <!-- Count cells in first row (before first nl) -->
      <sch:let name="first-row-cells" value="count($cell-tokens[following-sibling::dl:nl[1] is current()/dl:nl[1]])"/>
      
      <!-- Check that all subsequent rows have the same number of cells -->
      <sch:assert test="every $nl in dl:nl[position() > 1] satisfies
                        count($cell-tokens[preceding-sibling::dl:nl[1] is $nl/preceding-sibling::dl:nl[1] and
                                          following-sibling::dl:nl[1] is $nl]) = $first-row-cells">
        Table must follow the rectangular rule: all rows must have the same number of cells.
        First row has <sch:value-of select="$first-row-cells"/> cells, but at least one other row has a different count.
        Each row should have the same count of cell-starting tokens (fcel, ecel, ched, rhed, corn, srow, lcel, ucel, xcel) before each nl element.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- COMPONENT HEADER: Text must not precede component header elements -->
  <!-- Component header elements: xref, href, meta, location, layer (per XSD component_header group) -->
  <!-- This rule applies to regular semantic elements AND virtual <text> in lists/tables -->
  <!-- ============================================ -->

  <sch:pattern id="component-header-placement">
    <sch:rule context="dl:text | dl:heading | dl:code | dl:formula | dl:caption |
                       dl:page_header | dl:page_footer | dl:footnote | dl:picture |
                       dl:field_region | dl:field_heading | dl:field_item | dl:key | dl:value |
                       dl:list | dl:table | dl:group">
      <!-- Get all component header elements -->
      <sch:let name="header-elements" value="dl:xref | dl:href | dl:meta | dl:location | dl:layer"/>
      
      <!-- Get text nodes that appear before any component header element -->
      <sch:let name="text-before-header" value="text()[following-sibling::*[self::dl:xref or self::dl:href or self::dl:meta or self::dl:location or self::dl:layer]]"/>
      
      <sch:assert test="every $t in $text-before-header satisfies normalize-space($t) = ''">
        Component header elements (xref, href, meta, location, layer) must appear before any non-whitespace text content.
        Found non-whitespace text before component header: '<sch:value-of select="normalize-space(string-join($text-before-header, ''))"/>'
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- COMPONENT HEADER: xref and href are mutually exclusive -->
  <!-- ============================================ -->

  <sch:pattern id="xref-href-mutual-exclusivity">
    <sch:rule context="*[dl:xref and dl:href]">
      <sch:assert test="false()">
        Component head must not contain both xref and href elements; they are mutually exclusive.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- VIRTUAL TEXT IN LISTS: Component header must precede content -->
  <!-- A list item (content between <ldiv> siblings) acts as a virtual <text> -->
  <!-- and must follow the same component header rules -->
  <!-- ============================================ -->

  <sch:pattern id="list-virtual-text-component-header">
    <sch:rule context="dl:list/dl:ldiv">
      <!-- Get the next ldiv sibling or end of list -->
      <sch:let name="next-ldiv" value="following-sibling::dl:ldiv[1]"/>
      
      <!-- Get all content nodes between this ldiv and the next (or end of list) -->
      <sch:let name="item-content" value="if ($next-ldiv)
                                          then following-sibling::node()[following-sibling::dl:ldiv[1] is $next-ldiv]
                                          else following-sibling::node()"/>
      
      <!-- Get component header elements in this item -->
      <sch:let name="header-elements" value="$item-content[self::dl:xref or self::dl:href or self::dl:meta or self::dl:location or self::dl:layer]"/>
      
      <!-- Get index of first header element (1-based) -->
      <sch:let name="first-header-index" value="if ($header-elements)
                                                 then index-of($item-content, $header-elements[1])[1]
                                                 else 0"/>
      
      <!-- Get text nodes that appear before the first header -->
      <sch:let name="text-before-header" value="if ($first-header-index > 0)
                                                 then for $i in 1 to ($first-header-index - 1)
                                                      return $item-content[$i][self::text()][normalize-space(.) != '']
                                                 else ()"/>
      
      <sch:assert test="empty($text-before-header)">
        In list items (virtual text), component header elements (xref, href, meta, location, layer) must appear before any non-whitespace text content.
        Found non-whitespace text before component header: '<sch:value-of select="normalize-space(string-join($text-before-header, ''))"/>'
      </sch:assert>
    </sch:rule>
  </sch:pattern>

  <!-- ============================================ -->
  <!-- VIRTUAL TEXT IN TABLES: Component header must precede content -->
  <!-- A table cell (content after cell-starting tokens) acts as a virtual <text> -->
  <!-- and must follow the same component header rules -->
  <!-- ============================================ -->

  <sch:pattern id="table-virtual-text-component-header">
    <sch:rule context="dl:table/dl:fcel | dl:table/dl:ecel | dl:table/dl:ched |
                       dl:table/dl:rhed | dl:table/dl:corn | dl:table/dl:srow |
                       dl:table/dl:lcel | dl:table/dl:ucel | dl:table/dl:xcel">
      <!-- Get the next cell-starting token or table-ending token -->
      <sch:let name="next-token" value="following-sibling::*[self::dl:fcel or self::dl:ecel or self::dl:ched or
                                                              self::dl:rhed or self::dl:corn or self::dl:srow or
                                                              self::dl:lcel or self::dl:ucel or self::dl:xcel or
                                                              self::dl:nl][1]"/>
      
      <!-- Get all content nodes between this cell token and the next (or end of row/table) -->
      <sch:let name="cell-content" value="if ($next-token)
                                          then following-sibling::node()[following-sibling::*[. is $next-token]]
                                          else following-sibling::node()[not(following-sibling::dl:nl)]"/>
      
      <!-- Get component header elements in this cell -->
      <sch:let name="header-elements" value="$cell-content[self::dl:xref or self::dl:href or self::dl:meta or self::dl:location or self::dl:layer]"/>
      
      <!-- Get index of first header element (1-based) -->
      <sch:let name="first-header-index" value="if ($header-elements)
                                                 then index-of($cell-content, $header-elements[1])[1]
                                                 else 0"/>
      
      <!-- Get text nodes that appear before the first header -->
      <sch:let name="text-before-header" value="if ($first-header-index > 0)
                                                 then for $i in 1 to ($first-header-index - 1)
                                                      return $cell-content[$i][self::text()][normalize-space(.) != '']
                                                 else ()"/>
      
      <sch:assert test="empty($text-before-header)">
        In table cells (virtual text), component header elements (xref, href, meta, location, layer) must appear before any non-whitespace text content.
        Found non-whitespace text before component header: '<sch:value-of select="normalize-space(string-join($text-before-header, ''))"/>'
      </sch:assert>
    </sch:rule>
  </sch:pattern>

</sch:schema>
