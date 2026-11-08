#!/usr/bin/env python3
"""Update the README with today's Wordle word and its definition."""

import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from wordlewin import get_definition, get_wordle_word

README = Path(__file__).parent / "README.md"
START = "<!-- WORDLE:START -->"
END = "<!-- WORDLE:END -->"


def build_section(target_date):
    solution, _, data = get_wordle_word(target_date)
    lines = [
        START,
        f"## Today's Word ({target_date})",
        "",
        f"**{solution.upper()}** (Wordle #{data.get('days_since_launch', '?')}, "
        f"edited by {data.get('editor', 'unknown')})",
    ]
    definition = get_definition(solution)
    if definition:
        lines += ["", "```", definition, "```"]
    lines += ["", f"_Last updated automatically on {target_date}._", END]
    return "\n".join(lines)


def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).date().isoformat()
    section = build_section(target_date)
    text = README.read_text()

    if START in text and END in text:
        pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.DOTALL)
        text = pattern.sub(lambda _: section, text)
    else:
        text = text.rstrip() + "\n\n" + section + "\n"

    README.write_text(text)
    print(f"README updated for {target_date}")


if __name__ == "__main__":
    main()
