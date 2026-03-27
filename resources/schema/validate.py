#!/usr/bin/env python3
"""
XML Schema Validation Script
Validates an XML file against an XSD schema.
"""

import sys
from lxml import etree


def validate_xml(xml_file, xsd_file):
    """
    Validate an XML file against an XSD schema.

    Args:
        xml_file: Path to the XML file to validate
        xsd_file: Path to the XSD schema file

    Returns:
        bool: True if validation succeeds, False otherwise
    """
    try:
        # Parse the XSD schema
        with open(xsd_file, 'rb') as f:
            schema_root = etree.XML(f.read())
        schema = etree.XMLSchema(schema_root)

        # Parse the XML file
        with open(xml_file, 'rb') as f:
            xml_doc = etree.parse(f)

        # Validate
        is_valid = schema.validate(xml_doc)

        if is_valid:
            print(f"✓ Validation successful: '{xml_file}' is valid according to '{xsd_file}'")
            return True
        else:
            print(f"✗ Validation failed: '{xml_file}' is NOT valid according to '{xsd_file}'")
            print("\nValidation errors:")
            for error in schema.error_log:
                print(f"  Line {error.line}: {error.message}")
            return False

    except FileNotFoundError as e:
        print(f"Error: File not found - {e}")
        return False
    except etree.XMLSyntaxError as e:
        print(f"Error: XML syntax error - {e}")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False


def main():
    """Main entry point for the validation script."""
    if len(sys.argv) != 3:
        print("Usage: python validate.py <xml_file> <xsd_file>")
        print("Example: python validate.py test_input.xml doclang.xsd")
        sys.exit(1)

    xml_file = sys.argv[1]
    xsd_file = sys.argv[2]

    print(f"Validating XML file: {xml_file}")
    print(f"Against XSD schema: {xsd_file}")
    print("-" * 60)

    success = validate_xml(xml_file, xsd_file)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
