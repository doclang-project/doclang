"""
Saxon/C (saxonche) Schematron validation backend.

Transpiles .sch files to XSLT on-the-fly using XSLT 3.0 / XPath 3.1.
"""

from __future__ import annotations

import tempfile
from pathlib import Path

from lxml import etree

from doclang.backends._svrl import _svrl_failed_asserts_to_violations
from doclang.schematron import SchematronViolation, _require_saxonche_backend
from doclang.utils import _ensure_namespace, _parse_doclang_document, _write_xml_without_dtd

# ISO Schematron transpiler - converts .sch to XSLT 3.0
_ISO_SCHEMATRON_TRANSPILER = """<?xml version="1.0" encoding="UTF-8"?>
<xsl:stylesheet version="2.0"
    xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:sch="http://purl.oclc.org/dsdl/schematron"
    xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
    xmlns:dl="https://www.doclang.ai/ns/v0"
    xmlns:xsl2="http://www.w3.org/1999/XSL/Transform/alias"
    xmlns:svrl2="http://purl.oclc.org/dsdl/svrl/alias"
    xmlns:dl2="https://www.doclang.ai/ns/v0/alias">

  <xsl:namespace-alias stylesheet-prefix="xsl2" result-prefix="xsl"/>
  <xsl:namespace-alias stylesheet-prefix="svrl2" result-prefix="svrl"/>
  <xsl:namespace-alias stylesheet-prefix="dl2" result-prefix="dl"/>
  <xsl:output method="xml" indent="yes"/>

  <xsl:template match="/">
    <xsl2:stylesheet version="3.0"
        xmlns:svrl="http://purl.oclc.org/dsdl/svrl"
        xmlns:dl="https://www.doclang.ai/ns/v0">

      <xsl2:output method="xml" indent="yes"/>

      <!-- Main template -->
      <xsl2:template match="/">
        <svrl2:schematron-output>
          <xsl:apply-templates select="//sch:pattern" mode="apply-rules"/>
        </svrl2:schematron-output>
      </xsl2:template>

      <!-- Process patterns - generate templates at stylesheet level -->
      <xsl:apply-templates select="//sch:pattern" mode="generate-templates"/>

    </xsl2:stylesheet>
  </xsl:template>

  <!-- Generate apply-templates calls in main template -->
  <xsl:template match="sch:pattern" mode="apply-rules">
    <xsl:apply-templates select="sch:rule" mode="apply-rules"/>
  </xsl:template>

  <xsl:template match="sch:rule" mode="apply-rules">
    <xsl2:apply-templates select="//{@context}" mode="check-{generate-id()}"/>
  </xsl:template>

  <!-- Generate template definitions at stylesheet level -->
  <xsl:template match="sch:pattern" mode="generate-templates">
    <xsl:apply-templates select="sch:rule" mode="generate-templates"/>
  </xsl:template>

  <!-- Convert rule to template -->
  <xsl:template match="sch:rule" mode="generate-templates">
    <xsl2:template match="{@context}" mode="check-{generate-id()}">
      <xsl:apply-templates select="sch:let"/>
      <xsl:apply-templates select="sch:assert"/>
    </xsl2:template>
  </xsl:template>

  <!-- Convert let to variable -->
  <xsl:template match="sch:let">
    <xsl2:variable name="{@name}" select="{@value}"/>
  </xsl:template>

  <!-- Convert assert to if -->
  <xsl:template match="sch:assert">
    <xsl2:if test="not({@test})">
      <svrl2:failed-assert location="{{path()}}">
        <svrl2:text>
          <xsl:apply-templates/>
        </svrl2:text>
      </svrl2:failed-assert>
    </xsl2:if>
  </xsl:template>

  <!-- Copy value-of -->
  <xsl:template match="sch:value-of">
    <xsl2:value-of select="{@select}"/>
  </xsl:template>

  <!-- Copy text content -->
  <xsl:template match="text()">
    <xsl:value-of select="normalize-space(.)"/>
  </xsl:template>

</xsl:stylesheet>
"""


def _transpile_schematron_to_xslt(sch_file: Path, *, verbose: bool = False) -> str:
    _require_saxonche_backend()
    from saxonche import PySaxonProcessor

    if verbose:
        print(f"Transpiling Schematron: {sch_file}")

    with PySaxonProcessor(license=False) as proc:
        xslt_proc = proc.new_xslt30_processor()
        xslt_executable = xslt_proc.compile_stylesheet(stylesheet_text=_ISO_SCHEMATRON_TRANSPILER)
        result = xslt_executable.transform_to_string(source_file=str(sch_file))

        if not result:
            raise RuntimeError(f"Failed to transpile Schematron file: {sch_file}")

        return result


class SaxoncheValidator:
    """Schematron validator backed by Saxon/C (saxonche)."""

    def validate(
        self,
        xml_path: Path,
        *,
        schema_path: Path,
        allow_empty_namespace: bool = False,
        verbose: bool = False,
    ) -> list[SchematronViolation]:
        _require_saxonche_backend()
        from saxonche import PySaxonProcessor

        if verbose:
            print(f"Using Schematron file: {schema_path}")

        with open(xml_path, "rb") as f:
            xml_doc = _parse_doclang_document(f)

        if allow_empty_namespace:
            xml_doc = _ensure_namespace(xml_doc)

        with tempfile.NamedTemporaryFile(mode="wb", suffix=".xml", delete=True) as tmp:
            # Never re-emit a DOCTYPE: Saxon would otherwise expand entities.
            _write_xml_without_dtd(xml_doc, tmp)
            tmp.flush()
            tmp_xml_path = tmp.name

            with PySaxonProcessor(license=False) as proc:
                if verbose:
                    print(f"Using XSLT processor version: {proc.version}")

                xslt_proc = proc.new_xslt30_processor()

                if verbose:
                    print("Transpiling Schematron to XSLT 3.0...")

                xslt_text = _transpile_schematron_to_xslt(schema_path, verbose=verbose)

                if verbose:
                    print("Compiling generated XSLT...")

                xslt_executable = xslt_proc.compile_stylesheet(stylesheet_text=xslt_text)

                if verbose:
                    print("Executing Schematron validation...")

                result = xslt_executable.transform_to_string(source_file=tmp_xml_path)

                if not result:
                    return []

                result_doc = etree.fromstring(result.encode("utf-8"))
                return _svrl_failed_asserts_to_violations(result_doc)
