#!/usr/bin/env python3
"""Build a static GitHub Pages site showing today's Wordle word plus an archive of past words."""

import html
import json
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from wordlewin import get_definition, get_wordle_word

ROOT = Path(__file__).parent
OUT_DIR = ROOT / "site"
ARCHIVE = ROOT / "data" / "words.json"
LAUNCH = date(2021, 6, 19)

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Wordle word for {date}</title>
<script>
  (function () {{
    const t = localStorage.getItem('theme');
    if (t) document.documentElement.dataset.theme = t;
  }})();
</script>
<style>
  :root {{ color-scheme: light dark; --green: #6aaa64; }}
  :root[data-theme="light"] {{ color-scheme: light; }}
  :root[data-theme="dark"] {{ color-scheme: dark; }}
  body {{ background: Canvas; color: CanvasText; }}
  #theme {{ position: fixed; top: 1rem; right: 1rem; font-size: 1.2rem; line-height: 1; padding: .4rem .55rem;
           border: 1px solid #8886; border-radius: 6px; background: Canvas; color: CanvasText; cursor: pointer; }}
  body {{ font-family: system-ui, sans-serif; max-width: 42rem; margin: 3rem auto; padding: 0 1rem; line-height: 1.5; }}
  h1 {{ font-size: 1.1rem; font-weight: 600; opacity: .7; }}
  h2 {{ margin-top: 3rem; font-size: 1.2rem; }}
  .tiles {{ display: flex; gap: .4rem; margin: 1.5rem 0; cursor: pointer; }}
  .tile {{ width: 3.2rem; height: 3.2rem; display: grid; place-items: center; font-size: 1.8rem; font-weight: 700;
          color: #fff; background: var(--green); border-radius: 4px; text-transform: uppercase; }}
  .hidden .tile {{ color: transparent; background: #787c7e; }}
  .hint {{ font-size: .9rem; opacity: .6; }}
  .details {{ display: none; }}
  .revealed .details {{ display: block; }}
  pre {{ white-space: pre-wrap; font-size: .9rem; }}
  input {{ width: 100%; padding: .5rem; font-size: 1rem; box-sizing: border-box; margin-bottom: .5rem; }}
  .scroll {{ max-height: 24rem; overflow-y: auto; border: 1px solid #8884; border-radius: 6px; }}
  table {{ width: 100%; border-collapse: collapse; font-size: .8rem; }}
  th {{ position: sticky; top: 0; background: Canvas; }}
  td, th {{ text-align: left; padding: .2rem .5rem; border-bottom: 1px solid #8884; }}
  td.word {{ font-family: ui-monospace, monospace; font-weight: 700; letter-spacing: .1em; cursor: pointer; }}
  td.word:hover {{ color: var(--green); }}
  tr.def td {{ font-size: .75rem; white-space: pre-wrap; }}
  #count {{ font-size: .85rem; opacity: .6; }}
  footer {{ margin-top: 3rem; font-size: .8rem; opacity: .6; }}
  * {{ -webkit-tap-highlight-color: transparent; }}
  html {{ -webkit-text-size-adjust: 100%; text-size-adjust: 100%; }}
  @media (max-width: 600px) {{
    body {{ margin: 1rem auto 2rem; padding: 0 .75rem; }}
    h1 {{ padding-right: 3rem; font-size: 1rem; }}
    #theme {{ position: absolute; top: .6rem; right: .6rem; }}
    .tiles {{ gap: 1.5vw; margin: 1rem 0; }}
    .tile {{ width: min(16vw, 3.2rem); height: min(16vw, 3.2rem); font-size: min(9vw, 1.8rem); }}
    h2 {{ margin-top: 2rem; }}
    input {{ font-size: 16px; }}
    .scroll {{ max-height: 60vh; -webkit-overflow-scrolling: touch; }}
    td, th {{ padding: .45rem .5rem; }}
    pre {{ font-size: .8rem; }}
  }}
</style>
</head>
<body>
<button id="theme" type="button" aria-label="Toggle light/dark mode"></button>
<h1>Wordle #{number} &middot; {date}</h1>
<main id="root">
  <div class="tiles hidden" id="tiles" title="Click to reveal">{tiles}</div>
  <p class="hint" id="hint">Spoiler. Click the tiles to reveal.</p>
  <div class="details">
    <p>Edited by {editor}</p>
    {definition}
  </div>
</main>

<h2>Previous words</h2>
<input id="search" type="search" placeholder="Search by word, date or number&hellip;" autocomplete="off">
<p id="count"></p>
<div class="scroll">
<table>
  <thead><tr><th>#</th><th>Date</th><th>Word</th></tr></thead>
  <tbody id="archive">{rows}</tbody>
</table>
</div>

<footer>Updated automatically on {date} &middot; <a href="https://github.com/ZephrFish/wordlewin">wordlewin</a>
&middot; <a href="words.json">words.json</a> &middot; click a past word for its definition</footer>
<script>
  const themeBtn = document.getElementById('theme');
  const isDark = () => (document.documentElement.dataset.theme ||
    (matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light')) === 'dark';
  const syncIcon = () => {{
    themeBtn.textContent = isDark() ? '☀️' : '🌙';
    themeBtn.title = isDark() ? 'Switch to light mode' : 'Switch to dark mode';
  }};
  themeBtn.addEventListener('click', () => {{
    const next = isDark() ? 'light' : 'dark';
    document.documentElement.dataset.theme = next;
    localStorage.setItem('theme', next);
    syncIcon();
  }});
  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', syncIcon);
  syncIcon();

  document.getElementById('tiles').addEventListener('click', function () {{
    this.classList.remove('hidden');
    document.getElementById('root').classList.add('revealed');
    document.getElementById('hint').remove();
  }});

  const body = document.getElementById('archive');
  const rows = Array.from(body.querySelectorAll('tr'));
  const count = document.getElementById('count');
  const showCount = n => count.textContent = n + ' of ' + rows.length + ' words';
  showCount(rows.length);

  document.getElementById('search').addEventListener('input', function () {{
    const q = this.value.trim().toLowerCase();
    let n = 0;
    body.querySelectorAll('tr.def').forEach(r => r.remove());
    rows.forEach(r => {{
      const hit = !q || r.textContent.toLowerCase().includes(q);
      r.hidden = !hit;
      if (hit) n++;
    }});
    showCount(n);
  }});

  body.addEventListener('click', async function (e) {{
    const cell = e.target.closest('td.word');
    if (!cell) return;
    const row = cell.parentElement;
    const next = row.nextElementSibling;
    if (next && next.classList.contains('def')) {{ next.remove(); return; }}
    const defRow = document.createElement('tr');
    defRow.className = 'def';
    const td = document.createElement('td');
    td.colSpan = 3;
    td.textContent = 'Loading…';
    defRow.appendChild(td);
    row.after(defRow);
    try {{
      const res = await fetch('https://api.dictionaryapi.dev/api/v2/entries/en/' + cell.textContent.toLowerCase());
      if (!res.ok) throw new Error();
      const data = await res.json();
      td.textContent = data[0].meanings.map(m =>
        m.partOfSpeech + '\\n' + m.definitions.slice(0, 3).map(d => '  • ' + d.definition).join('\\n')
      ).join('\\n');
    }} catch {{
      td.textContent = 'No definition found.';
    }}
  }});
</script>
</body>
</html>
"""


def fetch_entry(day):
    """Fetch one day's puzzle as a compact archive record."""
    solution, _, data = get_wordle_word(day.isoformat())
    return {
        "date": day.isoformat(),
        "number": data.get("days_since_launch"),
        "solution": solution,
        "editor": data.get("editor"),
    }


def update_archive(target):
    """Load the archive and fetch any days missing between launch and the target date."""
    words = json.loads(ARCHIVE.read_text()) if ARCHIVE.exists() else []
    have = {w["date"] for w in words}
    missing = [
        LAUNCH + timedelta(days=i)
        for i in range((target - LAUNCH).days + 1)
        if (LAUNCH + timedelta(days=i)).isoformat() not in have
    ]
    if missing:
        print(f"Fetching {len(missing)} missing day(s)...")
        with ThreadPoolExecutor(max_workers=8) as pool:
            for entry in pool.map(fetch_entry, missing):
                words.append(entry)
    words.sort(key=lambda w: w["date"])
    ARCHIVE.parent.mkdir(exist_ok=True)
    ARCHIVE.write_text(json.dumps(words, indent=1) + "\n")
    return words


def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).date().isoformat()
    target = date.fromisoformat(target_date)
    words = update_archive(target)

    today = next(w for w in words if w["date"] == target_date)
    past = [w for w in reversed(words) if w["date"] < target_date]
    definition = get_definition(today["solution"])

    rows = "".join(
        f"<tr><td>{html.escape(str(w['number']))}</td><td>{w['date']}</td>"
        f"<td class=\"word\">{html.escape(w['solution'].upper())}</td></tr>"
        for w in past
    )

    page = TEMPLATE.format(
        date=html.escape(target_date),
        number=html.escape(str(today["number"])),
        editor=html.escape(today.get("editor") or "unknown"),
        tiles="".join(f'<div class="tile">{html.escape(c)}</div>' for c in today["solution"]),
        definition=f"<pre>{html.escape(definition)}</pre>" if definition else "<p>No definition found.</p>",
        rows=rows,
    )

    OUT_DIR.mkdir(exist_ok=True)
    (OUT_DIR / "index.html").write_text(page)
    (OUT_DIR / "words.json").write_text(json.dumps([w for w in words if w["date"] <= target_date], indent=1) + "\n")
    print(f"Site built for {target_date} with {len(past)} past words -> {OUT_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
