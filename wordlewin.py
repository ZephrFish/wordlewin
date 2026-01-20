#!/usr/bin/env python3
"""Fetch the Wordle word of the day from the NYTimes API."""

import argparse
import json
import urllib.request
from datetime import date


def get_wordle_word(target_date):
    """Fetch and return the Wordle word for a given date."""
    url = f"https://www.nytimes.com/svc/wordle/v2/{target_date}.json"

    with urllib.request.urlopen(url) as response:
        data = json.loads(response.read().decode())

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
    if args.full:
        print(f"\nFull response: {json.dumps(full_response, indent=2)}")


if __name__ == "__main__":
    main()
