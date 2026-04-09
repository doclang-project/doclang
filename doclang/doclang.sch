<?xml version="1.0" encoding="UTF-8"?>
<sch:schema xmlns:sch="http://purl.oclc.org/dsdl/schematron"
            xmlns:dl="https://www.doclang.ai/ns/v1"
            queryBinding="xslt3">

  <sch:title>Doclang Schematron Validation Rules (XSLT 3.0)</sch:title>

  <sch:ns prefix="dl" uri="https://www.doclang.ai/ns/v1"/>

  <!-- ============================================ -->
  <!-- HYPERLINK: Text before <uri> must be whitespace-only -->
  <!-- Uses XSLT 3.0 / XPath 3.1 features for cleaner expression -->
  <!-- ============================================ -->

  <sch:pattern id="hyperlink-uri-position">
    <sch:rule context="dl:hyperlink">
      <sch:let name="text-before-uri" value="text()[following-sibling::dl:uri]"/>
      <sch:assert test="every $t in $text-before-uri satisfies normalize-space($t) = ''">
        Hyperlink element must not contain non-whitespace text before the uri element.
        Found: '<sch:value-of select="string-join($text-before-uri, '')"/>'
      </sch:assert>
    </sch:rule>
  </sch:pattern>

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
      <sch:assert test="count(.//dl:otsl) >= 1">
        A floating_group with class="table" must contain at least one otsl element.
      </sch:assert>
    </sch:rule>
  </sch:pattern>

</sch:schema>
