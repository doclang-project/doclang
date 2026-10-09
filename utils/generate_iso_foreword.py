#!/usr/bin/env python3
"""
Script to replace the Foreword section of spec.md with the ISO one

Process:
1. Update the Foreword section in spec.md with the ISO foreword

Usage:
    python generate_iso_foreword.py
"""

import re
import sys
from pathlib import Path

foreword_content = """\
ISO (the International Organization for Standardization) and IEC (the International Electrotechnical Commission) form the specialized system for worldwide standardization. National bodies that are members of ISO or IEC participate in the development of International Standards through technical committees established by the respective organization to deal with particular fields of technical activity. ISO and IEC technical committees collaborate in fields of mutual interest. Other international organizations, governmental and non-governmental, in liaison with ISO and IEC, also take part in the work.

The procedures used to develop this document and those intended for its further maintenance are
described in the ISO/IEC Directives, Part 1. In particular, the different approval criteria needed for the different types of document should be noted (see [www.iso.org/directives](www.iso.org/directives) or [www.iec.ch/members_experts/refdocs](www.iec.ch/members_experts/refdocs)).

Attention is drawn to the possibility that some of the elements of this document may be the subject of patent rights. ISO and IEC shall not be held responsible for identifying any or all such patent rights. Details of any patent rights identified during the development of the document will be in the Introduction and/or on the ISO list of patent declarations received (see [www.iso.org/patents](www.iso.org/patents)) or the IEC list of patent declarations received (see [patents.iec.ch](patents.iec.ch)).

Any trade name used in this document is information given for the convenience of users and does not constitute an endorsement.

For an explanation of the voluntary nature of standards, the meaning of ISO specific terms and
expressions related to conformity assessment, as well as information about ISO's adherence to the World Trade Organization (WTO) principles in the Technical Barriers to Trade (TBT),
see [www.iso.org/iso/foreword.html](www.iso.org/iso/foreword.html). In the IEC, see [www.iec.ch/understanding-standards](www.iec.ch/understanding-standards).

This document was prepared by the Joint Development Foundation (JDF) (as Doclang Specification V@@@) and drafted in accordance with its editorial rules. @@@TO BE ADDED WHEN APPROPRIATE: It was adopted, under the JTC 1 PAS procedure, by Joint Technical Committee ISO/IEC JTC 1, _Information technology_.@@@

Any feedback or questions on this document should be directed to the user's national standards body. A complete listing of these bodies can be found at [www.iso.org/members.html](www.iso.org/members.html) and [www.iec.ch/national-committees](www.iec.ch/national-committees).\
"""


def update_foreword(foreword_content, spec_file):
    """Update the Foreword section in spec.md with ISO foreword"""
    print(f"\nUpdating Foreword in {spec_file}...")

    try:
        spec_content = Path(spec_file).read_text(encoding="utf-8")

        # Reference content sits between ### Reference and ### DocLang Archive Format
        reference_pattern = r"(## Foreword\n\n)"
        next_section_pattern = r"(## Introduction .*)"

        match_reference = re.search(reference_pattern, spec_content)
        match_next = re.search(next_section_pattern, spec_content)

        if not match_reference:
            print("Error: Could not find '### Reference' marker in spec.md")
            return False

        if not match_next:
            print("Error: Could not find '### DocLang Archive Format' marker in spec.md")
            return False

        # Reconstruct: through Reference header + new content + from next appendix section on
        before_reference = spec_content[: match_reference.end()]
        from_next_section = spec_content[match_next.start() :]
        # Strip trailing whitespace from reference content to avoid extra blank lines
        new_content = before_reference + foreword_content.rstrip() + "\n\n" + from_next_section

        # Write back to spec.md
        Path(spec_file).write_text(new_content, encoding="utf-8")
        print(f"✓ Successfully updated Reference in {spec_file}")
        return True

    except Exception as e:
        print(f"Error updating spec.md: {e}")
        return False


def generate_foreword() -> None:
    """Generate reference content from Excel input and update spec.md Reference section."""

    repo_root = Path(__file__).resolve().parent.parent
    spec_path = repo_root / "spec.md"

    if not update_foreword(foreword_content, str(spec_path)):
        raise RuntimeError("Failed to update Reference in spec.md")

    print("\nTask completed successfully!")
    print(f"- Updated: {spec_path}")


def main():
    if len(sys.argv) > 1:
        print("Error: No argument expected.")
        print("Usage: python generate_iso_foreword.py")
        sys.exit(1)

    try:
        generate_foreword()
    except (FileNotFoundError, NotADirectoryError, ValueError, RuntimeError) as exc:
        print(f"Error: {exc}")
        sys.exit(1)


if __name__ == "__main__":
    main()
