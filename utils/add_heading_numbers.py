"""Add hierarchical section numbers to headings in a Markdown file.

Also numbers EXAMPLE labels within each subsection when there is more than
one example in the same subsection (## or ### heading).

Numbering starts after ## Introduction (Introduction itself is not numbered)
and stops before ## Annexes.
Running the script multiple times is safe: existing numbers are stripped
before new ones are applied.

Usage:
    python add_heading_numbers.py [file]   (default: spec.md)
"""

import os
import re
import sys
import tempfile

# Matches an existing leading number on a heading, e.g. "1 " or "1.2 "
_EXISTING_NUMBER_RE = re.compile(r"^\d+(\.\d+)?\s+")


def _strip_number(title: str) -> str:
    """Remove a previously applied section number from a heading title."""
    return _EXISTING_NUMBER_RE.sub("", title)


def _number_examples(lines: list[str]) -> list[str]:
    """Add per-subsection numbers to EXAMPLE lines when there are multiples.

    A subsection boundary is any ## or ### heading.  Within each subsection
    the examples are counted; if there is only one, it is left as plain
    'EXAMPLE'.  Any previously applied number ('EXAMPLE 3') is stripped
    before counting so the function is idempotent.
    """
    # First pass: collect the raw 'EXAMPLE' line indices grouped by subsection.
    # A subsection starts at index 0 and resets on every ## / ### heading.
    subsection_groups: list[list[int]] = [[]]  # list of groups; each group is a list of line indices

    for i, line in enumerate(lines):
        if re.match(r"^#{2,3} ", line):
            subsection_groups.append([])
        elif re.match(r"^EXAMPLE(\s+\d+)?\s*$", line):
            subsection_groups[-1].append(i)

    # Second pass: rewrite lines in groups that have more than one example.
    result = list(lines)
    for group in subsection_groups:
        if len(group) > 1:
            for n, idx in enumerate(group, start=1):
                result[idx] = f"EXAMPLE {n}\n"
        elif len(group) == 1:
            # Strip any previously applied number (single example in section)
            result[group[0]] = "EXAMPLE\n"

    return result


def add_heading_numbers(path: str) -> None:
    """Rewrite *path* in-place, adding section numbers to headings."""
    in_scope = False  # True after (not including) ## Introduction
    in_annexes = False  # True after ## Annexes
    h2_counter = 0
    h3_counter = 0

    # Collect output in memory, then write atomically so a crash cannot
    # leave the file half-written.
    new_lines: list[str] = []

    with open(path, encoding="utf-8") as f:
        for line in f:
            # ## Annexes — stop numbering for all remaining lines
            if re.match(r"^## Annexes\s*$", line):
                in_annexes = True
                new_lines.append(line)
                continue

            if in_annexes:
                new_lines.append(line)
                continue

            # ## Introduction — emit as-is, then start numbering subsequent headings
            if re.match(r"^## (\d+\s+)?Introduction", line):
                new_lines.append(line)
                in_scope = True
                continue

            if in_scope:
                h3_match = re.fullmatch(r"(### )(.+)\n?", line)
                h2_match = re.fullmatch(r"(## )(.+)\n?", line)

                if h3_match:
                    # Check h3 before h2 because "### " also starts with "## "
                    h3_counter += 1
                    title = _strip_number(h3_match.group(2))
                    new_lines.append(f"### {h2_counter}.{h3_counter} {title}\n")
                    continue
                elif h2_match:
                    h2_counter += 1
                    h3_counter = 0
                    title = _strip_number(h2_match.group(2))
                    new_lines.append(f"## {h2_counter} {title}\n")
                    continue

            new_lines.append(line)

    new_lines = _number_examples(new_lines)

    # Write to a temp file in the same directory, then rename atomically
    dir_name = os.path.dirname(os.path.abspath(path))
    fd, tmp_path = tempfile.mkstemp(dir=dir_name, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as tmp_f:
            tmp_f.writelines(new_lines)
        os.replace(tmp_path, path)
    except Exception:
        os.unlink(tmp_path)
        raise

    print(f"Done — numbered {h2_counter} sections in {path}")


if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "spec.md"
    add_heading_numbers(target)
