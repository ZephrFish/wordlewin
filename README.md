# wordlewin

<!-- WORDLE:START -->
## Today's Word (2026-11-09)

**LOAMY** (Wordle #1969, edited by Tracy Bennett)

```
  adjective
    • Consisting of loam; partaking of the nature of loam; resembling loam.
```

_Last updated automatically on 2026-11-09._
<!-- WORDLE:END -->

Got bored so slapped together some python for [Wordle](https://www.nytimes.com/games/wordle/index.html) solver. It'll also pull a definition of the word of the day too along with synonyms.

## Live site

**https://zephrfish.github.io/wordlewin/** is rebuilt and deployed daily by GitHub Actions.

- **Spoiler-safe word of the day:** the tiles stay hidden until you click them (click again to hide), with the definition underneath.
- **Your local date:** the site switches to the new word at your local midnight, like Wordle itself, with a countdown to the next one. Today's word (in your time zone) never shows up in the archive, stats or practice mode.
- **Full archive:** every answer since #0 (CIGAR, 2021-06-19) in a searchable, scrollable table. Click a word for its definition.
- **Hide past answers:** blurs the archive until you tap a word, and search stops matching on words so it can't give them away.
- **Repeat markers:** answers NYT has used more than once get a ↻ marker listing the other dates.
- **Permalinks and sharing:** every day has a link like `#2024-02-14`. There's also a jump-to-date picker, and share buttons that use the phone's share sheet or copy the link on desktop.
- **Stats:** letter frequency, top first and last letters, repeated-letter rate, vowels per answer.
- **Practice mode:** guess a random past word, with letter hints, a reveal and a streak counter saved in your browser.
- **Keyboard shortcuts:** `/` search, `Space` reveal or hide, `D` jump to date, `R` practise, `T` theme.
- **Light/dark mode:** follows your system setting until you toggle it, and remembers your choice.
- **Works on mobile, installs as an app:** layout scales down to small phones, and you can add it to your home screen and use it offline.

### How it works

[`.github/workflows/daily-word.yml`](.github/workflows/daily-word.yml) runs every day at 00:15 UTC:

1. `update_readme.py` writes today's word into this README.
2. `build_site.py` adds any missing days to [`data/words.json`](data/words.json), the committed archive. It then builds the page in `site/` from the files in [`web/`](web/), adding the words for yesterday, today and tomorrow (UTC) so the page can pick the right one for each visitor's time zone.
3. The README and archive are committed, and `site/` is deployed to GitHub Pages.
4. If the run fails, it opens (or comments on) a "Daily Wordle run failed" issue.

To build the site locally:

```
python3 build_site.py              # today (UTC)
python3 build_site.py 2026-01-20   # a specific date
python3 -m http.server -d site     # preview at http://localhost:8000
```

The first run fetches the whole archive (about 2,000 requests, a minute or two). After that it only fetches new days.

## Usage
```
python3 wordlewin.py 2026-01-20
Date: 2026-01-20
Wordle word of the day: SULLY

python3 wordlewin.py 2026-01-20 --full                                                                                                                                              ─╯
Date: 2026-01-20
Wordle word of the day: SULLY

Full response: {
  "id": 2225,
  "solution": "sully",
  "print_date": "2026-01-20",
  "days_since_launch": 1676,
  "editor": "Tracy Bennett"
}
```
<img width="481" height="515" alt="image" src="https://github.com/user-attachments/assets/73175d55-7ae1-46c6-a83b-33ab1d8be3c3" />
