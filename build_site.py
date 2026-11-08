#!/usr/bin/env python3
"""Build a static GitHub Pages site: today's Wordle word, stats, and an archive of past words."""

import hashlib
import html
import json
import shutil
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from wordlewin import get_definition, get_wordle_word

ROOT = Path(__file__).parent
WEB = ROOT / "web"
OUT_DIR = ROOT / "site"
ARCHIVE = ROOT / "data" / "words.json"
LAUNCH = date(2021, 6, 19)
SITE_URL = "https://zephrfish.github.io/wordlewin/"
STATIC = ["style.css", "app.js", "sw.js", "manifest.webmanifest", "icon.svg",
          "icon-180.png", "icon-192.png", "icon-512.png"]


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
            words.extend(pool.map(fetch_entry, missing))
    words.sort(key=lambda w: w["date"])
    ARCHIVE.parent.mkdir(exist_ok=True)
    ARCHIVE.write_text(json.dumps(words, indent=1) + "\n")
    return words


def pct(n, total):
    return f"{100 * n / total:.0f}%"


def hbars(counter, total, limit=8):
    """Horizontal bar list (label, bar, visible value) for the top entries of a Counter."""
    top = counter.most_common(limit)
    peak = top[0][1]
    out = []
    for label, n in top:
        out.append(
            f'<span class="lbl">{label.upper()}</span>'
            f'<span class="track" title="{label.upper()}: {n} answers ({pct(n, total)})">'
            f'<i style="width:{100 * n / peak:.1f}%"></i></span>'
            f'<span class="val">{n}</span>'
        )
    return '<div class="bars">' + "".join(out) + "</div>"


def build_stats(past):
    """Stats over past answers only, so nothing here can spoil today's word."""
    total = len(past)
    sols = [w["solution"].lower() for w in past]
    contains = Counter(c for s in sols for c in set(s))
    first = Counter(s[0] for s in sols)
    last = Counter(s[-1] for s in sols)
    repeated = sum(1 for s in sols if len(set(s)) < len(s))
    vowels = sum(sum(c in "aeiou" for c in s) for s in sols) / total
    top_letter, top_letter_n = contains.most_common(1)[0]
    top_first, top_first_n = first.most_common(1)[0]

    tiles = [
        (f"{total:,}", "past answers"),
        (pct(repeated, total), "have a repeated letter"),
        (top_letter.upper(), f"most common letter, in {pct(top_letter_n, total)} of answers"),
        (top_first.upper(), f"most common first letter ({top_first_n})"),
        (f"{vowels:.1f}", "vowels per answer, on average"),
    ]
    tiles_html = '<div class="stat-tiles">' + "".join(
        f'<div class="stat"><b>{v}</b><span>{html.escape(l)}</span></div>' for v, l in tiles
    ) + "</div>"

    letters = sorted("abcdefghijklmnopqrstuvwxyz", key=lambda c: (-contains[c], c))
    peak = contains[letters[0]]
    cols = "".join(
        f'<div class="col" tabindex="0" aria-label="{c.upper()}: in {contains[c]} answers ({pct(contains[c], total)})">'
        f'<span class="tip">{c.upper()} &middot; {pct(contains[c], total)} ({contains[c]})</span>'
        f'<i style="height:{100 * contains[c] / peak:.1f}%"></i></div>'
        for c in letters
    )
    col_labels = "".join(f"<span>{c.upper()}</span>" for c in letters)

    return (
        tiles_html
        + '<p class="chart-title">Share of answers containing each letter</p>'
        + f'<div class="cols">{cols}</div><div class="col-labels">{col_labels}</div>'
        + '<div class="two-up">'
        + f'<div><p class="chart-title">Top first letters</p>{hbars(first, total)}</div>'
        + f'<div><p class="chart-title">Top last letters</p>{hbars(last, total)}</div>'
        + "</div>"
        + '<p class="note">Today\'s answer is left out of every stat. Hover or tap a column for its value.</p>'
    )


def render(template, **values):
    for key, value in values.items():
        template = template.replace("{{" + key + "}}", str(value))
    return template


def main():
    target_date = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).date().isoformat()
    target = date.fromisoformat(target_date)
    words = update_archive(target)

    today = next(w for w in words if w["date"] == target_date)
    past = [w for w in reversed(words) if w["date"] < target_date]
    definition = get_definition(today["solution"])

    rows = "".join(
        f'<tr id="d-{w["date"]}" data-d="{w["date"]}" data-n="{w["number"]}" '
        f'data-w="{html.escape(w["solution"].lower())}" data-k="{w["number"]} {w["date"]}">'
        f'<td>{w["number"]}</td><td><a href="#{w["date"]}">{w["date"]}</a></td>'
        f'<td class="word">{html.escape(w["solution"].upper())}</td></tr>'
        for w in past
    )

    page = render(
        (WEB / "template.html").read_text(),
        SITE_URL=SITE_URL,
        VERSION=hashlib.sha256((WEB / "app.js").read_bytes() + (WEB / "style.css").read_bytes()).hexdigest()[:10],
        DATE=html.escape(target_date),
        NUMBER=today["number"],
        EDITOR=html.escape(today.get("editor") or "unknown"),
        TILES="".join(f'<div class="tile">{html.escape(c)}</div>' for c in today["solution"]),
        DEFINITION=f"<pre>{html.escape(definition)}</pre>" if definition else "<p>No definition found.</p>",
        PAST_COUNT=f"{len(past):,}",
        STATS=build_stats(past),
        ROWS=rows,
    )

    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir()
    (OUT_DIR / "index.html").write_text(page)
    (OUT_DIR / "words.json").write_text(
        json.dumps([w for w in words if w["date"] <= target_date], indent=1) + "\n"
    )
    for name in STATIC:
        shutil.copy2(WEB / name, OUT_DIR / name)
    # Bump the service-worker cache name each build so clients pick up the new day.
    sw = OUT_DIR / "sw.js"
    sw.write_text(sw.read_text().replace("wordlewin-v1", f"wordlewin-{target_date}"))
    print(f"Site built for {target_date} with {len(past)} past words -> {OUT_DIR / 'index.html'}")


if __name__ == "__main__":
    main()
