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

    # Drop any existing section, wherever it sits, then insert at the top.
    pattern = re.compile(r"\n*" + re.escape(START) + r".*?" + re.escape(END) + r"\n*", re.DOTALL)
    text = pattern.sub("\n\n", text).strip("\n")

    # Place the section directly under the H1 title (or at the very top if there isn't one).
    lines = text.split("\n")
    if lines and lines[0].startswith("# "):
        title, rest = lines[0], "\n".join(lines[1:]).lstrip("\n")
        text = f"{title}\n\n{section}\n\n{rest}"
    else:
        text = f"{section}\n\n{text}"

    README.write_text(text.rstrip("\n") + "\n")
    print(f"README updated for {target_date}")


if __name__ == "__main__":
    main()
