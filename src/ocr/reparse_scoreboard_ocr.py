"""Re-parse existing scoreboard OCR CSV without running OCR again."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

from src.ocr.scoreboard_text import parse_clock, parse_score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Re-parse score and clock fields from raw OCR text.")
    parser.add_argument("--input", required=True, type=Path, help="Existing OCR CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Re-parsed OCR CSV.")
    parser.add_argument("--max-score", type=int, default=20)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"OCR CSV not found: {args.input}")

    with args.input.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for required in ["raw_text", "parsed_clock", "parsed_home_score", "parsed_away_score"]:
        if required not in fieldnames:
            fieldnames.append(required)

    parsed_score_rows = 0
    parsed_clock_rows = 0
    for row in rows:
        raw_text = row.get("raw_text", "")
        home_score, away_score = parse_score(raw_text, max_score=args.max_score)
        clock = parse_clock(raw_text)
        row["parsed_home_score"] = home_score
        row["parsed_away_score"] = away_score
        row["parsed_clock"] = clock
        if home_score and away_score:
            parsed_score_rows += 1
        if clock:
            parsed_clock_rows += 1

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"input rows: {len(rows)}")
    print(f"parsed score rows: {parsed_score_rows}")
    print(f"parsed clock rows: {parsed_clock_rows}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
