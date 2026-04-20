#!/usr/bin/env python3
"""
Script to generate markdown documentation from an Excel file

Process:
1. Use docling to convert xlsx to intermediate markdown
2. Parse the intermediate markdown to extract elements and attributes
3. Generate structured output with H3 for categories, H4 for elements, and attributes arrays

Usage:
    python generate_reference.py <input_directory> <output_directory>

    Arguments:
    - input_directory: Directory containing the Excel file with element definitions
      (also may contain .dclg.xml and .png files for examples)
    - output_directory: Directory where reference.md will be written
      (will be created if it doesn't exist)
"""

import re
import os
import sys
from collections import defaultdict
from pathlib import Path
from docling.document_converter import DocumentConverter


def normalize_element_name(element):
    """Keep element names as-is (with backticks)"""
    # Don't remove backticks - keep them for element tags
    return element


def normalize_category_name(category):
    """Normalize category names by removing square and round brackets and their contents, then format for display"""
    import re
    # Remove content in square brackets including the brackets: [00], [01a], etc.
    normalized = re.sub(r'\[[\w]+\]\s*', '', category)
    # Remove content in round brackets including the brackets: (top), (inner), (outer)
    normalized = re.sub(r'\s*\([^)]*\)', '', normalized)
    # Clean up extra whitespace
    normalized = ' '.join(normalized.split())
    # Capitalize each word
    if normalized:
        normalized = ' '.join(word.capitalize() for word in normalized.split())
    return normalized


def format_category_for_display(category):
    """Format category name for display by adding 'Elements' suffix"""
    return category + " Elements"


def run_docling_conversion(input_file, output_dir):
    """Use docling API to convert xlsx to markdown"""
    print(f"Converting {input_file} to markdown using docling...")

    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    try:
        # Initialize the document converter
        converter = DocumentConverter()

        # Convert the document
        result = converter.convert(input_file)

        # Export to markdown
        markdown_content = result.document.export_to_markdown()

        # Write to intermediate.md
        intermediate_md_file = os.path.join(output_dir, "intermediate.md")
        with open(intermediate_md_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)

        print(f"Conversion successful. Output: {intermediate_md_file}")
        return intermediate_md_file

    except Exception as e:
        print(f"Error during docling conversion: {e}")
        return None


def parse_intermediate_markdown(md_file):
    """Parse the intermediate markdown file to extract elements and attributes"""
    with open(md_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # Data structures to hold parsed information
    elements_by_category = defaultdict(list)
    attributes_by_element = defaultdict(list)
    content_types_by_element = defaultdict(dict)  # Store content type info for each element
    category_order = []  # Preserve order from categories table
    category_descriptions = {}  # Store category descriptions
    element_descriptions = {}  # Store element descriptions
    element_contexts = {}  # Store element contexts
    element_context_header = None  # Store the context column header name

    # Parse the markdown table format
    lines = content.split('\n')

    # Find where the categories, elements, and attributes tables are
    in_categories_table = False
    in_elements_table = False
    in_attributes_table = False
    categories_header_seen = False
    elements_header_seen = False
    attributes_header_seen = False
    content_type_columns = {}  # Initialize to avoid unbound variable

    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            continue

        # Check if we're in the categories table (has category and description columns)
        if '| category' in line and '| description' in line and not categories_header_seen:
            in_categories_table = True
            in_elements_table = False
            in_attributes_table = False
            categories_header_seen = True
            continue

        # Check if we're in the elements table (has Category column first)
        if '| Category' in line and '| Element' in line and not elements_header_seen:
            in_elements_table = True
            in_categories_table = False
            in_attributes_table = False
            elements_header_seen = True
            # Parse the header to find content type columns and context column
            header_parts = [p.strip() for p in line.split('|')]
            content_type_columns = {}
            for idx, header in enumerate(header_parts):
                if header.startswith('[Content] '):
                    # Extract the content type name (just remove the prefix)
                    content_type = header.replace('[Content] ', '').strip()
                    content_type_columns[idx] = content_type
                elif idx == 4 and header:  # Element context is typically at index 4
                    # Store the context column header and normalize it
                    # Remove "Element " prefix if present and capitalize
                    element_context_header = header.replace('Element ', '').strip().title()
            continue

        # Check if we're in the attributes table (has Element and Attribute columns, but no Category)
        if '| Element' in line and '| Attribute' in line and '| Category' not in line:
            in_attributes_table = True
            in_elements_table = False
            in_categories_table = False
            attributes_header_seen = True
            continue

        # Skip separator lines
        if line.strip().startswith('|---'):
            continue

        # Parse categories table rows
        if in_categories_table and line.strip().startswith('|') and not line.strip().startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:  # At least: empty, category, description
                canonical_category = parts[1]
                description = parts[2] if len(parts) > 2 else ''
                if canonical_category and canonical_category != 'category':
                    # Store the canonical category name in order
                    # Capitalize each word for display
                    formatted_category = ' '.join(word.capitalize() for word in canonical_category.split())
                    if formatted_category not in category_order:
                        category_order.append(formatted_category)
                        category_descriptions[formatted_category] = description
            # Check if we've reached the end of categories table
            if i + 1 < len(lines) and not lines[i + 1].strip():
                in_categories_table = False

        # Parse elements table rows
        if in_elements_table and line.strip().startswith('|') and not line.strip().startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 5:  # At least: empty, Category, Element, Element description, Element context
                prefixed_category = parts[1]
                element = parts[2]
                element_description = parts[3] if len(parts) > 3 else ''
                element_context = parts[4] if len(parts) > 4 else ''
                if prefixed_category and element and prefixed_category != 'Category':
                    # Normalize the category to get canonical name
                    canonical_category = normalize_category_name(prefixed_category)
                    elements_by_category[canonical_category].append(element)
                    # Store element description and context
                    element_descriptions[element] = element_description
                    element_contexts[element] = element_context

                    # Store content type information
                    for idx, content_type in content_type_columns.items():
                        if idx < len(parts):
                            content_types_by_element[element][content_type] = parts[idx]
            # Check if we've reached the end of elements table (blank line or new table)
            if i + 1 < len(lines) and not lines[i + 1].strip():
                in_elements_table = False

        # Parse attributes table rows - store full row data
        if in_attributes_table and line.strip().startswith('|') and not line.strip().startswith('|---'):
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 3:  # At least: empty, Element, Attribute, ...
                element = parts[1]
                if element and element != 'Element':
                    # Store the entire row data as a dict
                    attr_data = {
                        'attribute': parts[2] if len(parts) > 2 else '',
                        'required': parts[3] if len(parts) > 3 else '',
                        'allowed_values': parts[4] if len(parts) > 4 else '',
                        'description': parts[5] if len(parts) > 5 else ''
                    }
                    attributes_by_element[element].append(attr_data)

    return elements_by_category, attributes_by_element, content_types_by_element, category_order, category_descriptions, element_descriptions, element_contexts, element_context_header


def load_example_for_element(element_name, input_dir, iso_standard_path):
    """Load example from INPUT_DIR/examples/ if it exists

    Returns a tuple: (xml_content, image_path) or (None, None) if no example exists

    The image_path will be relative from iso-standard.md location to the PNG file
    in INPUT_DIR/examples/.
    """
    # Remove backticks and angle brackets from element name to get filename
    clean_name = element_name.replace('`', '').replace('<', '').replace('>', '')

    # Look for files in INPUT_DIR/examples/
    examples_dir = Path(input_dir) / 'examples'
    xml_file = examples_dir / f"{clean_name}.dclg.xml"

    xml_content = None
    image_path = None

    # Check for XML file
    if xml_file.exists():
        with open(xml_file, 'r', encoding='utf-8') as f:
            xml_content = f.read().strip()

    # Look for PNG file in the examples directory
    png_file = examples_dir / f"{clean_name}.png"
    if png_file.exists():
        # Calculate relative path from iso-standard.md to the PNG file
        png_file_abs = png_file.resolve()
        iso_standard_dir = Path(iso_standard_path).resolve().parent

        # Calculate relative path from iso-standard.md directory to PNG file
        image_path = os.path.relpath(png_file_abs, iso_standard_dir)

    # Return tuple if we have XML content
    if xml_content:
        return xml_content, image_path

    return None, None


def create_element_anchor(element_name):
    """Create anchor link for an element"""
    # Remove backticks and angle brackets, convert to lowercase, replace spaces with hyphens
    return element_name.replace('`', '').replace('<', '').replace('>', '').lower().replace(' ', '-')


def linkify_element_references(text, all_elements):
    """Replace element references like `<element>` with markdown links"""
    if not text:
        return text

    # Create a pattern that matches `<element_name>` format
    for element in all_elements:
        # Extract the element name without backticks for the pattern
        element_clean = element.replace('`', '')
        # Create the anchor
        anchor = create_element_anchor(element)
        # Replace occurrences of the element reference with a link
        # Use word boundaries to avoid partial matches
        pattern = re.escape(element)
        replacement = f"[{element}](#{anchor})"
        text = re.sub(pattern, replacement, text)

    return text


def generate_output_markdown(elements_by_category, attributes_by_element, content_types_by_element, category_order, category_descriptions, element_descriptions, element_contexts, element_context_header, input_dir, output_dir, output_file, iso_standard_path):
    """Generate the final doclang_out.md file"""
    print(f"Generating {output_file}...")

    with open(output_file, 'w', encoding='utf-8') as f:
        # Use category order from categories table, or fall back to sorted keys
        if category_order:
            # Only include categories that have elements
            ordered_categories = [cat for cat in category_order if cat in elements_by_category]
        else:
            ordered_categories = sorted(elements_by_category.keys())

        # Collect all elements for linkification
        all_elements = []
        for category in ordered_categories:
            all_elements.extend(elements_by_category[category])

        for category in ordered_categories:
            # Write category as H3
            # Format category for display (add "Elements" suffix)
            display_category = format_category_for_display(category)
            f.write(f"### {display_category}\n\n")

            # Write category description if available
            if category in category_descriptions and category_descriptions[category]:
                f.write(f"{category_descriptions[category]}\n\n")

            # Get elements for this category
            elements = elements_by_category[category]

            for element in elements:
                # Write element as H4
                # Normalize element name (keep backticks)
                normalized_element = normalize_element_name(element)
                f.write(f"#### {normalized_element}\n\n")

                # Write element description if available (with linkified element references)
                if element in element_descriptions and element_descriptions[element]:
                    description = linkify_element_references(element_descriptions[element], all_elements)
                    f.write(f"{description}\n\n")

                # Write element context if available (with linkified element references)
                if element in element_contexts and element_contexts[element]:
                    # Use the dynamically extracted header name, or default to "Context"
                    context_heading = element_context_header if element_context_header else "Context"
                    f.write(f"##### {context_heading}\n\n")
                    context = linkify_element_references(element_contexts[element], all_elements)
                    f.write(f"{context}\n\n")

                # Write attributes table if they exist
                if element in attributes_by_element:
                    attributes = attributes_by_element[element]
                    f.write("##### Attributes\n\n")

                    # Write table header
                    f.write("| Attribute | Required / Optional | Allowed Values | Description |\n")
                    f.write("|-----------|----------|----------------|-------------|\n")

                    # Write table rows (with linkified element references in description)
                    for attr_data in attributes:
                        attr_name = normalize_element_name(attr_data['attribute'])
                        required = linkify_element_references(attr_data['required'], all_elements)
                        allowed_values = linkify_element_references(attr_data['allowed_values'], all_elements)
                        description = linkify_element_references(attr_data['description'], all_elements)
                        f.write(f"| {attr_name} | {required} | {allowed_values} | {description} |\n")

                    f.write("\n")
                else:
                    f.write("##### Attributes\n\nNone\n\n")

                # Write content types table if they exist
                if element in content_types_by_element and content_types_by_element[element]:
                    content_types = content_types_by_element[element]
                    f.write("##### Allowed Content Types\n\n")

                    # If XML content is not allowed, the element is empty:
                    # omit the table and render a note. Otherwise, remove only
                    # the XML content column and keep the remaining table.
                    xml_content_value = content_types_by_element[element].get('XML content', '')
                    xml_content_allowed = linkify_element_references(xml_content_value, all_elements).lower() == 'true'

                    if not xml_content_allowed:
                        f.write("None (empty element).\n\n")
                    else:
                        headers = []
                        values = []

                        for header, v in content_types.items():
                            if header == 'XML content':
                                continue

                            headers.append(header)
                            v_linked = linkify_element_references(v, all_elements)
                            if v_linked.lower() == 'true':
                                values.append('Allowed')
                            elif v_linked.lower() == 'false':
                                values.append('Not allowed')
                            else:
                                values.append(v_linked)

                        # Write table header
                        f.write("| " + " | ".join(headers) + " |\n")
                        f.write("| " + " | ".join(["---"] * len(headers)) + " |\n")

                        # Write single data row
                        f.write("| " + " | ".join(values) + " |\n\n")

                # Check for and include example if it exists
                xml_content, image_path = load_example_for_element(element, input_dir, iso_standard_path)
                if xml_content:
                    f.write("##### Example\n\n")

                    # Include image if available
                    if image_path:
                        f.write("<details>\n")
                        f.write("  <summary>Show document picture</summary>\n")
                        f.write("\n")
                        f.write(f'  <img src="{image_path}" width="700">\n')
                        f.write("\n")
                        f.write("</details>\n\n")

                    # Include XML content wrapped in markdown code block
                    f.write("```xml\n")
                    f.write(f"{xml_content}\n")
                    f.write("```\n\n")

    print(f"Output file generated: {output_file}")


def main():
    # Check if both input and output directories are provided
    if len(sys.argv) < 3:
        print("Error: Both input and output directory paths are required.")
        print("Usage: python generate_reference.py <input_directory> <output_directory>")
        sys.exit(1)

    input_dir = sys.argv[1]
    output_dir_arg = sys.argv[2]

    # Validate input directory exists
    if not os.path.exists(input_dir):
        print(f"Error: Input directory '{input_dir}' not found.")
        sys.exit(1)

    if not os.path.isdir(input_dir):
        print(f"Error: '{input_dir}' is not a directory.")
        sys.exit(1)

    # Find Excel file in the directory (exclude temporary files starting with ~$)
    excel_files = [f for f in os.listdir(input_dir)
                   if f.lower().endswith(('.xlsx', '.xls')) and not f.startswith('~$')]

    if not excel_files:
        print(f"Error: No Excel file (.xlsx or .xls) found in '{input_dir}'")
        sys.exit(1)

    if len(excel_files) > 1:
        print(f"Error: Multiple Excel files found in '{input_dir}': {', '.join(excel_files)}")
        print("Please ensure only one Excel file is present in the directory.")
        sys.exit(1)

    # Use the found Excel file
    input_file = os.path.join(input_dir, excel_files[0])
    base_name = os.path.splitext(excel_files[0])[0]

    # Get the repository root (parent of utils directory where this script is located)
    script_dir = Path(__file__).resolve().parent
    repo_root = script_dir.parent

    # Save intermediate markdown in build/ subdirectory at repo root
    intermediate_dir = repo_root / 'build'
    intermediate_dir.mkdir(exist_ok=True)

    # Use the output directory provided as argument (create if doesn't exist)
    output_dir = Path(output_dir_arg).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'reference.md'

    # Path to iso-standard.md (at repo root)
    iso_standard_path = repo_root / 'iso-standard.md'

    # Step 1: Convert xlsx to intermediate markdown using docling
    intermediate_file = run_docling_conversion(input_file, str(intermediate_dir))
    if not intermediate_file:
        print("Failed to convert xlsx to markdown. Exiting.")
        return

    # Step 2: Parse the intermediate markdown
    elements_by_category, attributes_by_element, content_types_by_element, category_order, category_descriptions, element_descriptions, element_contexts, element_context_header = parse_intermediate_markdown(intermediate_file)

    # Step 3: Generate the output markdown
    generate_output_markdown(elements_by_category, attributes_by_element, content_types_by_element, category_order, category_descriptions, element_descriptions, element_contexts, element_context_header, input_dir, str(output_dir), str(output_file), str(iso_standard_path))

    print("\nProcess completed successfully!")
    print(f"- Input: {input_file}")
    print(f"- Intermediate: {intermediate_file}")
    print(f"- Output: {output_file}")


if __name__ == '__main__':
    main()
