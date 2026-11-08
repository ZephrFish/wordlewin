#!/usr/bin/env python3
"""Build a static GitHub Pages site showing the Wordle word of the day."""

import html
import sys
from datetime import datetime, timezone
from pathlib import Path

from wordlewin import get_definition, get_wordle_word

OUT_DIR = Path(__file__).parent / "site"

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wordle word for {date}</title>
<style>
  :root {{ color-scheme: light dark; --green: #6aaa64; }}
  body {{ font-family: system-ui, sans-serif; max-width: 42rem; margin: 3rem auto; padding: 0 1rem; line-height: 1.5; }}
  h1 {{ font-size: 1.1rem; font-weight: 600; opacity: .7; }}
  .tiles {{ display: flex; gap: .4rem; margin: 1.5rem 0; cursor: pointer; }}
  .tile {{ width: 3.2rem; height: 3.2rem; display: grid; place-items: center; font-size: 1.8rem; font-weight: 700;
          color: #fff; background: var(--green); border-radius: 4px; text-transform: uppercase; }}
  .hidden .tile {{ color: transparent; background: #787c7e; }}
  .hint {{ font-size: .9rem; opacity: .6; }}
  .details {{ display: none; }}
  .revealed .details {{ display: block; }}
  pre {{ white-space: pre-wrap; font-size: .9rem; }}
  footer {{ margin-top: 3rem; font-size: .8rem; opacity: .6; }}
</style>
</head>
<body>
<h1>Wordle #{number} &middot; {date}</h1>
<main id="root">
  <div class="tiles hidden" id="tiles" title="Click to reveal">{tiles}</div>
  <p class="hint" id="hint">Spoiler. Click the tiles to reveal.</p>
  <div class="details">
    <p>Edited by {editor}</p>
    {definition}
  </div>
</main>
<footer>Updated automatically on {date} &middot; <a href="https://github.com/ZephrFish/wordlewin">wordlewin</a></footer>
<script>
  document.getElementById('tiles').addEventListener('click', function () {{
    this.classList.remove('hidden');
    document.getElementById('root').classList.add('revealed');
    document.getElementById('hint').remove();
  }});
</script>
</body>
</html>
"""


def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).date().isoformat()
    solution, _, data = get_wordle_word(target_date)
    definition = get_definition(solution)

    page = TEMPLATE.format(
        date=html.escape(target_date),
        number=html.escape(str(data.get("days_since_launch", "?"))),
        editor=html.escape(data.get("editor", "unknown")),
        tiles="".join(f'<div class="tile">{html.escape(c)}</div>' for c in solution),
        definition=f"<pre>{html.escape(definition)}</pre>" if definition else "<p>No definition found.</p>",
    )

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "index.html").write_text(page)
    print(f"Site built for {target_date} -> {OUT_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
