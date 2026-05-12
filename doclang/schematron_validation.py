"""
Schematron validation utilities for DocLang.

This module provides Schematron validation by transpiling .sch files to XSLT
on-the-fly using XSLT 3.0 / XPath 3.1.
"""

from pathlib import Path
from lxml import etree
from saxonche import PySaxonProcessor
import tempfile

from doclang.utils import _ensure_namespace


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


def _transpile_schematron_to_xslt(sch_file, verbose=False):
    """
    Transpile Schematron (.sch) to XSLT 3.0 on-the-fly.

    Args:
        sch_file: Path to Schematron file
        verbose: Print progress messages

    Returns:
        str: Generated XSLT stylesheet as string
    """
    if verbose:
        print(f"Transpiling Schematron: {sch_file}")

    with PySaxonProcessor(license=False) as proc:
        xslt_proc = proc.new_xslt30_processor()

        # Compile the transpiler
        xslt_executable = xslt_proc.compile_stylesheet(
            stylesheet_text=_ISO_SCHEMATRON_TRANSPILER
        )

        # Transform Schematron to XSLT
        result = xslt_executable.transform_to_string(source_file=str(sch_file))

        if not result:
            raise RuntimeError(f"Failed to transpile Schematron file: {sch_file}")

        return result


def _validate_with_schematron(xml_file, sch_file=None, allow_empty_namespace=False, verbose=False):
    """
    Validate XML against Schematron rules using XSLT 3.0 / XPath 3.1.

    Transpiles the Schematron file to XSLT on-the-fly, then validates.

    Args:
        xml_file: Path to XML file to validate
        sch_file: Path to Schematron file (default: doclang/doclang.sch)
        allow_empty_namespace: If True, automatically add DocLang namespace if missing
        verbose: Print detailed progress messages

    Returns:
        tuple: (is_valid: bool, failed_asserts: list)
    """
    # Default to doclang.sch in same directory as this module
    if sch_file is None:
        sch_file = Path(__file__).parent / "doclang.sch"

    if verbose:
        print(f"Using Schematron file: {sch_file}")

    try:
        # Load and optionally ensure namespace
        with open(xml_file, 'rb') as f:
            xml_doc = etree.parse(f)

        if allow_empty_namespace:
            xml_doc = _ensure_namespace(xml_doc)

        # Write to temporary file for Saxon processing
        # Note: delete=True (default) but we need to close before Saxon can read
        with tempfile.NamedTemporaryFile(mode='wb', suffix='.xml', delete=True) as tmp:
            xml_doc.write(tmp, encoding='utf-8', xml_declaration=True)
            tmp.flush()  # Ensure data is written
            tmp_xml_path = tmp.name

            # File is still open but flushed, Saxon can read it
            with PySaxonProcessor(license=False) as proc:
                if verbose:
                    print(f"Using XSLT processor version: {proc.version}")

                # Get XSLT 3.0 processor (supports XPath 3.1)
                xslt_proc = proc.new_xslt30_processor()

                # Transpile Schematron to XSLT
                if verbose:
                    print("Transpiling Schematron to XSLT 3.0...")

                xslt_text = _transpile_schematron_to_xslt(sch_file, verbose=verbose)

                # Compile the generated XSLT stylesheet
                if verbose:
                    print("Compiling generated XSLT...")

                xslt_executable = xslt_proc.compile_stylesheet(stylesheet_text=xslt_text)

                # Transform XML
                if verbose:
                    print("Executing Schematron validation...")

                result = xslt_executable.transform_to_string(source_file=tmp_xml_path)

                # Parse result
                if result:
                    result_doc = etree.fromstring(result.encode('utf-8'))
                    failed_asserts = result_doc.findall(".//{http://purl.oclc.org/dsdl/svrl}failed-assert")

                    is_valid = len(failed_asserts) == 0
                    return is_valid, failed_asserts
                else:
                    # No output means validation passed
                    return True, []

        # Temporary file automatically deleted when exiting context manager

    except Exception as e:
        if verbose:
            print(f"✗ Error during Schematron validation: {e}")
            import traceback
            traceback.print_exc()
        raise
