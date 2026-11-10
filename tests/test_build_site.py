"""Tests for the tomorrow's-word logic in build_site.py.

Covers the pure helpers (tomorrow_date_of, pick_day, tomorrow_template_values)
directly, plus candidate_days' window extension and its defensive handling of
a day that fails to fetch (e.g. NYT hasn't published it yet). get_wordle_word
and get_definition are mocked: they're the external-API boundary, not internal
logic, so mocking them here is in bounds.
"""

import sys
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import build_site  # noqa: E402


class TomorrowDateOfTests(unittest.TestCase):
    def test_returns_iso_string_for_next_day(self):
        self.assertEqual(build_site.tomorrow_date_of(date(2026, 11, 9)), "2026-11-10")

    def test_crosses_month_boundary(self):
        self.assertEqual(build_site.tomorrow_date_of(date(2026, 11, 30)), "2026-12-01")


class PickDayTests(unittest.TestCase):
    def setUp(self):
        self.days = [
            {"date": "2026-11-08", "number": 1000},
            {"date": "2026-11-09", "number": 1001},
            {"date": "2026-11-10", "number": 1002},
        ]

    def test_finds_matching_entry(self):
        self.assertEqual(build_site.pick_day(self.days, "2026-11-10"), self.days[2])

    def test_returns_none_when_missing(self):
        self.assertIsNone(build_site.pick_day(self.days, "2026-12-25"))

    def test_returns_none_on_empty_list(self):
        self.assertIsNone(build_site.pick_day([], "2026-11-10"))


class TomorrowTemplateValuesTests(unittest.TestCase):
    def test_present_entry_renders_real_values(self):
        entry = {
            "number": 1234,
            "solution": "CRANE",
            "editor": "Jane Doe",
            "definition": "A tall wading bird.",
        }
        values = build_site.tomorrow_template_values(entry, "2026-11-10")
        self.assertEqual(values["TOMORROW_NUMBER"], 1234)
        self.assertEqual(values["TOMORROW_DATE"], "2026-11-10")
        self.assertEqual(
            values["TOMORROW_TILES"],
            '<div class="tile">C</div><div class="tile">R</div><div class="tile">A</div>'
            '<div class="tile">N</div><div class="tile">E</div>',
        )
        self.assertEqual(values["TOMORROW_DEFINITION"], "A tall wading bird.")
        self.assertEqual(values["TOMORROW_EDITOR"], "Jane Doe")

    def test_missing_entry_falls_back_to_placeholders(self):
        values = build_site.tomorrow_template_values(None, "2026-11-10")
        self.assertEqual(values["TOMORROW_NUMBER"], "?")
        self.assertEqual(values["TOMORROW_DATE"], "2026-11-10")
        self.assertEqual(values["TOMORROW_TILES"], "")
        self.assertEqual(values["TOMORROW_DEFINITION"], "Not available yet.")
        self.assertEqual(values["TOMORROW_EDITOR"], "unknown")

    def test_entry_with_missing_definition_and_editor_falls_back(self):
        entry = {"number": 5, "solution": "ABCDE", "editor": None, "definition": None}
        values = build_site.tomorrow_template_values(entry, "2026-11-10")
        self.assertEqual(values["TOMORROW_DEFINITION"], "Not available yet.")
        self.assertEqual(values["TOMORROW_EDITOR"], "unknown")

    def test_escapes_html_in_date(self):
        values = build_site.tomorrow_template_values(None, '2026-11-10"><script>')
        self.assertNotIn("<script>", values["TOMORROW_DATE"])


class CandidateDaysTests(unittest.TestCase):
    def setUp(self):
        self.target = date(2026, 11, 9)
        # @mock-exempt: get_definition calls the dictionaryapi.dev HTTP API; external boundary.
        self.def_patch = patch.object(build_site, "get_definition", return_value="def")
        self.def_patch.start()
        self.addCleanup(self.def_patch.stop)

    def _entry(self, offset_days, from_target=None):
        base = from_target or self.target
        d = base + build_site.timedelta(days=offset_days)
        return {"date": d.isoformat(), "number": 1000 + offset_days, "solution": "WORDS", "editor": "Ed"}

    def test_window_covers_yesterday_through_day_after_tomorrow(self):
        words = [self._entry(o) for o in (-1, 0, 1, 2)]
        # @mock-exempt: fetch_entry wraps get_wordle_word, an HTTP call to the NYT API.
        with patch.object(build_site, "fetch_entry") as fetch:
            days = build_site.candidate_days(words, self.target)
        fetch.assert_not_called()
        self.assertEqual(
            [d["date"] for d in days],
            ["2026-11-08", "2026-11-09", "2026-11-10", "2026-11-11"],
        )
        self.assertTrue(all("definition" in d for d in days))

    def test_fetches_a_missing_day_in_the_window(self):
        words = [self._entry(o) for o in (-1, 0)]  # tomorrow (+1) and +2 missing
        fetched = {"date": "2026-11-10", "number": 1001, "solution": "FETCH", "editor": "Ed"}

        def fake_fetch(day):
            if day.isoformat() == "2026-11-10":
                return fetched
            raise RuntimeError("not published yet")

        # @mock-exempt: fetch_entry wraps get_wordle_word, an HTTP call to the NYT API.
        with patch.object(build_site, "fetch_entry", side_effect=fake_fetch):
            days = build_site.candidate_days(words, self.target)
        dates = [d["date"] for d in days]
        self.assertIn("2026-11-10", dates)
        self.assertNotIn("2026-11-11", dates)  # +2 raised, so it's skipped
        self.assertEqual(len(days), 3)

    def test_unfetchable_day_is_skipped_not_raised(self):
        words = [self._entry(o) for o in (-1, 0, 1)]  # +2 missing and will fail to fetch

        # @mock-exempt: fetch_entry wraps get_wordle_word, an HTTP call to the NYT API.
        with patch.object(build_site, "fetch_entry", side_effect=RuntimeError("boom")):
            days = build_site.candidate_days(words, self.target)  # must not raise
        self.assertEqual(len(days), 3)
        self.assertNotIn("2026-11-11", [d["date"] for d in days])


if __name__ == "__main__":
    unittest.main()
