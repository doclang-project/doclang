#!/usr/bin/env python3
"""
Script to generate markdown documentation from an Excel file and update spec.md

Process:
1. Use docling to convert xlsx to intermediate markdown
2. Parse the intermediate markdown to extract elements and attributes
3. Generate structured output with H3 for categories, H4 for elements, and attributes arrays
4. Update Appendix A in spec.md with the generated content

Usage:
    python generate_reference.py <input_directory>

    Arguments:
    - input_directory: Directory containing the Excel file with element definitions
      (also may contain .dclg.xml and .png files for examples)
"""

import os
import re
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
    normalized = re.sub(r"\[[\w]+\]\s*", "", category)
    # Remove content in round brackets including the brackets: (top), (inner), (outer)
    normalized = re.sub(r"\s*\([^)]*\)", "", normalized)
    # Clean up extra whitespace
    normalized = " ".join(normalized.split())
    # Capitalize each word
    if normalized:
        normalized = " ".join(word.capitalize() for word in normalized.split())
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
        with open(intermediate_md_file, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        print(f"Conversion successful. Output: {intermediate_md_file}")
        return intermediate_md_file

    except Exception as e:
        print(f"Error during docling conversion: {e}")
        return None


def parse_intermediate_markdown(md_file):
    """Parse the intermediate markdown file to extract elements and attributes"""
    with open(md_file, encoding="utf-8") as f:
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
    tbd_column_idx = None  # Index of the TBD column in the elements table (if present)

    # Parse the markdown table format
    lines = content.split("\n")

    # Find where the categories, elements, and attributes tables are
    in_categories_table = False
    in_elements_table = False
    in_attributes_table = False
    categories_header_seen = False
    elements_header_seen = False
    content_type_columns = {}  # Initialize to avoid unbound variable

    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            continue

        # Check if we're in the categories table (has category and description columns)
        if "| category" in line and "| description" in line and not categories_header_seen:
            in_categories_table = True
            in_elements_table = False
            in_attributes_table = False
            categories_header_seen = True
            continue

        # Check if we're in the elements table (has Category column first)
        if "| Category" in line and "| Element" in line and not elements_header_seen:
            in_elements_table = True
            in_categories_table = False
            in_attributes_table = False
            elements_header_seen = True
            # Parse the header to find content type columns and context column
            header_parts = [p.strip() for p in line.split("|")]
            content_type_columns = {}
            for idx, header in enumerate(header_parts):
                if header == "TBD":
                    tbd_column_idx = idx
                elif header.startswith("[Content] "):
                    # Extract the content type name (just remove the prefix)
                    content_type = header.replace("[Content] ", "").strip()
                    content_type_columns[idx] = content_type
                elif idx == 4 and header:  # Element context is typically at index 4
                    # Store the context column header and normalize it
                    # Remove "Element " prefix if present and capitalize
                    element_context_header = header.replace("Element ", "").strip().title()
            continue

        # Check if we're in the attributes table (has Element and Attribute columns, but no Category)
        if "| Element" in line and "| Attribute" in line and "| Category" not in line:
            in_attributes_table = True
            in_elements_table = False
            in_categories_table = False
            continue

        # Skip separator lines
        if line.strip().startswith("|---"):
            continue

        # Parse categories table rows
        if in_categories_table and line.strip().startswith("|") and not line.strip().startswith("|---"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:  # At least: empty, category, description
                canonical_category = parts[1]
                description = parts[2] if len(parts) > 2 else ""
                if canonical_category and canonical_category != "category":
                    # Store the canonical category name in order
                    # Capitalize each word for display
                    formatted_category = " ".join(word.capitalize() for word in canonical_category.split())
                    if formatted_category not in category_order:
                        category_order.append(formatted_category)
                        category_descriptions[formatted_category] = description
            # Check if we've reached the end of categories table
            if i + 1 < len(lines) and not lines[i + 1].strip():
                in_categories_table = False

        # Parse elements table rows
        if in_elements_table and line.strip().startswith("|") and not line.strip().startswith("|---"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 5:  # At least: empty, Category, Element, Element description, Element context
                prefixed_category = parts[1]
                element = parts[2]
                element_description = parts[3] if len(parts) > 3 else ""
                element_context = parts[4] if len(parts) > 4 else ""
                if (
                    tbd_column_idx is not None
                    and tbd_column_idx < len(parts)
                    and parts[tbd_column_idx].strip().upper() == "TRUE"
                ):
                    continue
                if prefixed_category and element and prefixed_category != "Category":
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
        if in_attributes_table and line.strip().startswith("|") and not line.strip().startswith("|---"):
            parts = [p.strip() for p in line.split("|")]
            if len(parts) >= 3:  # At least: empty, Element, Attribute, ...
                element = parts[1]
                if element and element != "Element":
                    # Store the entire row data as a dict
                    attr_data = {
                        "attribute": parts[2] if len(parts) > 2 else "",
                        "required": parts[3] if len(parts) > 3 else "",
                        "allowed_values": parts[4] if len(parts) > 4 else "",
                        "description": parts[5] if len(parts) > 5 else "",
                    }
                    attributes_by_element[element].append(attr_data)

    return (
        elements_by_category,
        attributes_by_element,
        content_types_by_element,
        category_order,
        category_descriptions,
        element_descriptions,
        element_contexts,
        element_context_header,
    )


def load_example_for_element(element_name, input_dir, spec_path):
    """Load example from INPUT_DIR/examples/ if it exists

    Returns a tuple: (xml_content, image_path) or (None, None) if no example exists

    The image_path will be relative from spec.md location to the PNG file
    in INPUT_DIR/examples/.
    """
    # Remove backticks and angle brackets from element name to get filename
    clean_name = element_name.replace("`", "").replace("<", "").replace(">", "")

    # Look for files in INPUT_DIR/examples/
    examples_dir = Path(input_dir) / "examples"
    xml_file = examples_dir / f"{clean_name}.dclg.xml"

    xml_content = None
    image_path = None

    # Check for XML file
    if xml_file.exists():
        with open(xml_file, encoding="utf-8") as f:
            xml_content = f.read().strip()

    # Look for PNG file in the examples directory
    png_file = examples_dir / f"{clean_name}.png"
    if png_file.exists():
        # Calculate relative path from spec.md to the PNG file
        png_file_abs = png_file.resolve()
        spec_dir = Path(spec_path).resolve().parent

        # Calculate relative path from spec.md directory to PNG file
        image_path = os.path.relpath(png_file_abs, spec_dir)

    # Return tuple if we have XML content
    if xml_content:
        return xml_content, image_path

    return None, None


def create_element_anchor(element_name):
    """Create anchor link for an element"""
    # Remove backticks and angle brackets, convert to lowercase, replace spaces with hyphens
    return element_name.replace("`", "").replace("<", "").replace(">", "").lower().replace(" ", "-")


def element_tag_name(element):
    """Extract tag name from a spreadsheet element label such as `<doclang>`."""
    return element.replace("`", "").strip("<>")


def linkify_element_references(text, all_elements):
    """Replace element references like `<element>` with markdown links."""
    if not text:
        return text

    # Longest tag names first so e.g. `<page_break>` is not partially matched as `<page>`
    unique_elements = list(dict.fromkeys(all_elements))
    sorted_elements = sorted(unique_elements, key=lambda e: len(element_tag_name(e)), reverse=True)

    for element in sorted_elements:
        anchor = create_element_anchor(element)
        link = f"[{element}](#{anchor})"
        bare_form = f"<{element_tag_name(element)}>"

        # Backtick-wrapped form from the spreadsheet (e.g. `<doclang>`)
        text = re.sub(re.escape(element), link, text)

        # Bare angle-bracket form; skip when already inside a markdown link or backticks
        text = re.sub(
            r"(?<!\[)(?<!`)" + re.escape(bare_form) + r"(?!\]\(#)",
            link,
            text,
        )

    return text


def generate_reference_content(
    elements_by_category,
    attributes_by_element,
    content_types_by_element,
    category_order,
    category_descriptions,
    element_descriptions,
    element_contexts,
    element_context_header,
    input_dir,
    spec_path,
):
    """Generate the reference markdown content as a string"""
    print("Generating reference content...")

    output_lines = []

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
        output_lines.append(f"### {display_category}\n\n")

        # Write category description if available (with linkified element references)
        if category_descriptions.get(category):
            description = linkify_element_references(category_descriptions[category], all_elements)
            output_lines.append(f"{description}\n\n")

        # Get elements for this category
        elements = elements_by_category[category]

        for element in elements:
            # Write element as H4
            # Normalize element name (keep backticks)
            normalized_element = normalize_element_name(element)
            output_lines.append(f"#### {normalized_element}\n\n")

            # Write element description if available (with linkified element references)
            if element_descriptions.get(element):
                description = linkify_element_references(element_descriptions[element], all_elements)
                output_lines.append(f"{description}\n\n")

            # Write element context if available (with linkified element references)
            if element_contexts.get(element):
                # Use the dynamically extracted header name, or default to "Context"
                context_heading = element_context_header if element_context_header else "Context"
                output_lines.append(f"##### {context_heading}\n\n")
                context = linkify_element_references(element_contexts[element], all_elements)
                output_lines.append(f"{context}\n\n")

            # Write attributes table if they exist
            if element in attributes_by_element:
                attributes = attributes_by_element[element]
                output_lines.append("##### Attributes\n\n")

                # Write table header
                output_lines.append("| Attribute | Required / Optional | Allowed Values | Description |\n")
                output_lines.append("|-----------|----------|----------------|-------------|\n")

                # Write table rows (with linkified element references in description)
                for attr_data in attributes:
                    attr_name = normalize_element_name(attr_data["attribute"])
                    required = linkify_element_references(attr_data["required"], all_elements)
                    allowed_values = linkify_element_references(attr_data["allowed_values"], all_elements)
                    description = linkify_element_references(attr_data["description"], all_elements)
                    output_lines.append(f"| {attr_name} | {required} | {allowed_values} | {description} |\n")

                output_lines.append("\n")
            else:
                output_lines.append("##### Attributes\n\nNone\n\n")

            # Write content types table if they exist
            if content_types_by_element.get(element):
                content_types = content_types_by_element[element]
                output_lines.append("##### Allowed Content Types\n\n")

                # If XML content is not allowed, the element is empty:
                # omit the table and render a note. Otherwise, create a vertical
                # table with Content Type and Allowed/Not allowed columns.
                xml_content_value = content_types_by_element[element].get("XML content", "")
                xml_content_allowed = linkify_element_references(xml_content_value, all_elements).lower() == "true"

                if not xml_content_allowed:
                    output_lines.append("None (empty element).\n\n")
                else:
                    # Write table header (vertical format)
                    output_lines.append("| Content Type | Allowed / Not allowed |\n")
                    output_lines.append("| --- | --- |\n")

                    # Write one row per content type
                    for header, v in content_types.items():
                        if header == "XML content":
                            continue

                        v_linked = linkify_element_references(v, all_elements)
                        if v_linked.lower() == "true":
                            status = "Allowed"
                        elif v_linked.lower() == "false":
                            status = "Not allowed"
                        else:
                            status = v_linked

                        output_lines.append(f"| {header} | {status} |\n")

                    output_lines.append("\n")

            # Check for and include example if it exists
            xml_content, image_path = load_example_for_element(element, input_dir, spec_path)
            if xml_content:
                output_lines.append("##### Example\n\n")

                # Include image if available
                if image_path:
                    output_lines.append("<details>\n")
                    output_lines.append("  <summary>Show document picture</summary>\n")
                    output_lines.append("\n")
                    output_lines.append(f'  <img src="{image_path}" width="700">\n')
                    output_lines.append("\n")
                    output_lines.append("</details>\n\n")

                # Include XML content wrapped in markdown code block
                output_lines.append("```xml\n")
                output_lines.append(f"{xml_content}\n")
                output_lines.append("```\n\n")

    print("Reference content generated successfully")
    return "".join(output_lines)


def update_spec_appendix(reference_content, spec_file):
    """Update Appendix A in spec.md with generated reference content"""
    import re

    print(f"\nUpdating Appendix A in {spec_file}...")

    try:
        spec_content = Path(spec_file).read_text(encoding="utf-8")

        # Find Appendix A and B section markers
        appendix_a_pattern = r"(## Appendix A: Reference\n\n)"
        appendix_b_pattern = r"(## Appendix B:)"

        match_a = re.search(appendix_a_pattern, spec_content)
        match_b = re.search(appendix_b_pattern, spec_content)

        if not match_a:
            print("Error: Could not find '## Appendix A: Reference' marker in spec.md")
            return False

        if not match_b:
            print("Error: Could not find '## Appendix B:' marker in spec.md")
            return False

        # Reconstruct the file: before Appendix A + reference content + from Appendix B onwards
        before_appendix_a = spec_content[: match_a.end()]
        from_appendix_b = spec_content[match_b.start() :]
        # Strip trailing whitespace from reference content to avoid extra blank lines
        new_content = before_appendix_a + reference_content.rstrip() + "\n\n" + from_appendix_b

        # Write back to spec.md
        Path(spec_file).write_text(new_content, encoding="utf-8")
        print(f"✓ Successfully updated Appendix A in {spec_file}")
        return True

    except Exception as e:
        print(f"Error updating spec.md: {e}")
        return False


def generate_reference(input_dir: str | Path) -> None:
    """Generate reference content from Excel input and update spec.md Appendix A."""
    input_dir = Path(input_dir)

    if not input_dir.exists():
        raise FileNotFoundError(f"Input directory '{input_dir}' not found.")
    if not input_dir.is_dir():
        raise NotADirectoryError(f"'{input_dir}' is not a directory.")

    excel_files = [
        f for f in input_dir.iterdir() if f.suffix.lower() in (".xlsx", ".xls") and not f.name.startswith("~$")
    ]

    if not excel_files:
        raise FileNotFoundError(f"No Excel file (.xlsx or .xls) found in '{input_dir}'")
    if len(excel_files) > 1:
        names = ", ".join(f.name for f in excel_files)
        raise ValueError(
            f"Multiple Excel files found in '{input_dir}': {names}. "
            "Please ensure only one Excel file is present in the directory."
        )

    input_file = excel_files[0]

    repo_root = Path(__file__).resolve().parent.parent
    intermediate_dir = repo_root / "build"
    intermediate_dir.mkdir(exist_ok=True)
    spec_path = repo_root / "spec.md"

    intermediate_file = run_docling_conversion(str(input_file), str(intermediate_dir))
    if not intermediate_file:
        raise RuntimeError("Failed to convert xlsx to markdown.")

    (
        elements_by_category,
        attributes_by_element,
        content_types_by_element,
        category_order,
        category_descriptions,
        element_descriptions,
        element_contexts,
        element_context_header,
    ) = parse_intermediate_markdown(intermediate_file)

    reference_content = generate_reference_content(
        elements_by_category,
        attributes_by_element,
        content_types_by_element,
        category_order,
        category_descriptions,
        element_descriptions,
        element_contexts,
        element_context_header,
        str(input_dir),
        str(spec_path),
    )

    if not update_spec_appendix(reference_content, str(spec_path)):
        raise RuntimeError("Failed to update Appendix A in spec.md")

    print("\nAll tasks completed successfully!")
    print(f"- Input: {input_file}")
    print(f"- Intermediate: {intermediate_file}")
    print(f"- Updated: {spec_path}")


def main():
    if len(sys.argv) < 2:
        print("Error: Input directory path is required.")
        print("Usage: python generate_reference.py <input_directory>")
        sys.exit(1)

    try:
        generate_reference(sys.argv[1])
    except (FileNotFoundError, NotADirectoryError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
