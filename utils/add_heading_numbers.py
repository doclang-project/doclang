"""Add hierarchical section numbers to headings in a Markdown file.

Also numbers EXAMPLE labels within each subsection when there is more than
one example in the same subsection (## or ### heading).

Numbering starts after ## Introduction (Introduction itself is not numbered)
and stops before ## Annexes.
Running the script multiple times is safe: existing numbers are stripped
before new ones are applied.

Because a heading number changes the heading's anchor (e.g. "Formatting" ->
"811-formatting"), internal links of the form "](#anchor)" that point to a
numbered heading are rewritten to the new anchor.  Links using either the
un-numbered anchor or a previously numbered anchor are updated.

Usage:
    python add_heading_numbers.py [file]   (default: spec.md)
"""

import os
import re
import sys
import tempfile

# Matches an existing leading number on a heading, e.g. "1 " or "1.2 "
_EXISTING_NUMBER_RE = re.compile(r"^\d+(\.\d+)?\s+")


# Matches an internal Markdown link target, e.g. "](#formatting)"
_INTERNAL_LINK_RE = re.compile(r"(\]\(#)([^)\s]+)(\))")


def _strip_number(title: str) -> str:
    """Remove a previously applied section number from a heading title."""
    return _EXISTING_NUMBER_RE.sub("", title)


def _slugify(title: str) -> str:
    """Build a GitHub-style anchor from a heading title."""
    slug = re.sub(r"[^\w\s-]", "", title.lower()).strip()
    return re.sub(r"\s", "-", slug)


def _update_links(lines: list[str], anchor_map: dict[str, str]) -> list[str]:
    """Rewrite '](#old)' link targets according to *anchor_map*."""
    if not anchor_map:
        return lines

    def repl(m: re.Match) -> str:
        return m.group(1) + anchor_map.get(m.group(2), m.group(2)) + m.group(3)

    return [_INTERNAL_LINK_RE.sub(repl, line) for line in lines]


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


def _record_anchors(
    anchor_map: dict[str, str],
    base_slug_count: dict[str, int],
    current_title: str,
    base_title: str,
    new_title: str,
) -> None:
    """Record how a numbered heading's anchor changes.

    Un-numbered anchors shared by several numbered headings are ambiguous and
    are left untouched (the link is not rewritten).
    """
    new_slug = _slugify(new_title)
    base_slug = _slugify(base_title)
    current_slug = _slugify(current_title)

    base_slug_count[base_slug] = base_slug_count.get(base_slug, 0) + 1
    if base_slug_count[base_slug] > 1:
        print(f"Warning: ambiguous anchor '#{base_slug}'; links to it left unchanged")
        anchor_map.pop(base_slug, None)
    else:
        anchor_map[base_slug] = new_slug

    if current_slug != base_slug:
        anchor_map[current_slug] = new_slug


def add_heading_numbers(path: str) -> None:
    """Rewrite *path* in-place, adding section numbers to headings."""
    in_scope = False  # True after (not including) ## Introduction
    in_annexes = False  # True after ## Annexes
    h2_counter = 0
    h3_counter = 0
    # Anchor changes: slug before numbering -> slug after numbering.
    # Both the un-numbered slug and the slug of the heading as currently
    # written in the file (possibly carrying an older number) are recorded.
    anchor_map: dict[str, str] = {}
    base_slug_count: dict[str, int] = {}

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
                    new_title = f"{h2_counter}.{h3_counter} {title}"
                    new_lines.append(f"### {new_title}\n")
                    _record_anchors(anchor_map, base_slug_count, h3_match.group(2), title, new_title)
                    continue
                elif h2_match:
                    h2_counter += 1
                    h3_counter = 0
                    title = _strip_number(h2_match.group(2))
                    new_title = f"{h2_counter} {title}"
                    new_lines.append(f"## {new_title}\n")
                    _record_anchors(anchor_map, base_slug_count, h2_match.group(2), title, new_title)
                    continue

            new_lines.append(line)

    new_lines = _number_examples(new_lines)
    new_lines = _update_links(new_lines, anchor_map)

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
