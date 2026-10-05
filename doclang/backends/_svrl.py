"""SVRL parsing helpers for Schematron backends."""

from __future__ import annotations

from lxml import etree

from doclang.schematron import SchematronViolation

_SVRL_NS = "http://purl.oclc.org/dsdl/svrl"


def _failed_assert_to_violation(assert_elem: etree._Element) -> SchematronViolation:
    text_elem = assert_elem.find(f"{{{_SVRL_NS}}}text")
    message = text_elem.text if text_elem is not None and text_elem.text else "No message"
    return SchematronViolation(
        location=assert_elem.get("location"),
        message=message,
        rule_id=assert_elem.get("id"),
        test=assert_elem.get("test"),
    )


def _svrl_failed_asserts_to_violations(svrl_root: etree._Element) -> list[SchematronViolation]:
    failed_asserts = svrl_root.findall(f".//{{{_SVRL_NS}}}failed-assert")
    return [_failed_assert_to_violation(elem) for elem in failed_asserts]
