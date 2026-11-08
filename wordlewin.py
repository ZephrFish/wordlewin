#!/usr/bin/env python3
"""Fetch the Wordle word of the day from the NYTimes API."""

import argparse
import json
import urllib.request
from datetime import date

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/142.0.0.0 Safari/537.36 wordlewin/1.0"
    )
}


def fetch_json(url):
    """GET a URL and decode the JSON body."""
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode())


def get_definition(word):
    """Fetch and return formatted definitions of a word from the free dictionary API."""
    url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"

    try:
        data = fetch_json(url)

        if not data or len(data) == 0:
            return None

        meanings = data[0].get("meanings", [])
        if not meanings:
            return None

        lines = []
        for meaning in meanings:
            part_of_speech = meaning.get("partOfSpeech", "")
            definitions = meaning.get("definitions", [])
            if not definitions:
                continue

            # Show up to 3 definitions per part of speech
            for i, defn in enumerate(definitions[:3]):
                definition_text = defn.get("definition", "")
                example = defn.get("example", "")
                synonyms = defn.get("synonyms", [])

                if i == 0:
                    lines.append(f"  {part_of_speech}")
                lines.append(f"    • {definition_text}")

                if example:
                    lines.append(f"      Example: \"{example}\"")

                if synonyms:
                    # Show up to 5 synonyms
                    syns = ", ".join(synonyms[:5])
                    if len(synonyms) > 5:
                        syns += ", ..."
                    lines.append(f"      Synonyms: {syns}")

        return "\n".join(lines) if lines else None

    except (urllib.error.URLError, ValueError):
        return None


def get_wordle_word(target_date):
    """Fetch and return the Wordle word for a given date."""
    url = f"https://www.nytimes.com/svc/wordle/v2/{target_date}.json"

    data = fetch_json(url)

    return data.get("solution"), target_date, data


def main():
    parser = argparse.ArgumentParser(description="Fetch the Wordle word of the day")
    parser.add_argument(
        "date",
        nargs="?",
        default=date.today().isoformat(),
        help="Date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Show the full API response",
    )
    args = parser.parse_args()

    solution, target_date, full_response = get_wordle_word(args.date)

    print(f"Date: {target_date}")
    print(f"Wordle word of the day: {solution.upper()}")

    definition = get_definition(solution)
    if definition:
        print(f"\nDefinition:")
        print(definition)

    if args.full:
        print(f"\nFull response: {json.dumps(full_response, indent=2)}")


if __name__ == "__main__":
    main()
