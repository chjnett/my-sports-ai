"""Extract text-cue events from OCR rows."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


TOKEN_RE = re.compile(r"[A-Za-z][A-Za-z'.-]*")
DEFAULT_STOPWORDS = {
    "CHE",
    "BUR",
    "RUR",
    "CORN",
    "CORNER",
    "CORNERS",
    "CORNRS",
    "THE",
    "AND",
    "VS",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract player/event text cues from OCR CSV.")
    parser.add_argument("--ocr", required=True, type=Path, help="OCR CSV with raw_text column.")
    parser.add_argument("--output", required=True, type=Path, help="Output text cue event CSV.")
    parser.add_argument("--team-tokens", default="CHE,BUR", help="Comma-separated team abbreviations to ignore.")
    parser.add_argument("--stopwords", default="", help="Extra comma-separated uppercase tokens to ignore.")
    parser.add_argument("--min-token-length", type=int, default=4)
    parser.add_argument("--merge-gap-sec", type=float, default=20.0)
    return parser.parse_args()


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_stopwords(team_tokens: str, extra_stopwords: str) -> set[str]:
    stopwords = set(DEFAULT_STOPWORDS)
    for raw in [team_tokens, extra_stopwords]:
        for token in raw.split(","):
            token = token.strip().upper()
            if token:
                stopwords.add(token)
    return stopwords


def normalize_token(token: str) -> str:
    return re.sub(r"[^A-Z]", "", token.upper())


def extract_tokens(text: str, stopwords: set[str], min_token_length: int) -> list[str]:
    tokens: list[str] = []
    for match in TOKEN_RE.finditer(text):
        token = normalize_token(match.group(0))
        if len(token) < min_token_length:
            continue
        if token in stopwords:
            continue
        if token.isdigit():
            continue
        tokens.append(token)
    return tokens


def should_merge(previous: dict[str, str], current: dict[str, str], merge_gap_sec: float) -> bool:
    if previous.get("half") != current.get("half"):
        return False
    if previous.get("cue_text") != current.get("cue_text"):
        return False
    return parse_float(current.get("timestamp_sec")) - parse_float(previous.get("end_timestamp_sec")) <= merge_gap_sec


def merge_events(events: list[dict[str, str]], merge_gap_sec: float) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    for event in sorted(events, key=lambda row: (row.get("half", ""), parse_float(row.get("timestamp_sec")))):
        if merged and should_merge(merged[-1], event, merge_gap_sec):
            merged[-1]["end_timestamp_sec"] = event["timestamp_sec"]
            merged[-1]["evidence_count"] = str(int(merged[-1]["evidence_count"]) + 1)
            merged[-1]["raw_text"] = event["raw_text"]
            merged[-1]["source_image"] = event["source_image"]
            continue
        merged.append(event)
    return merged


def main() -> None:
    args = parse_args()
    if not args.ocr.exists():
        raise SystemExit(f"OCR CSV not found: {args.ocr}")

    stopwords = parse_stopwords(args.team_tokens, args.stopwords)
    with args.ocr.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    events: list[dict[str, str]] = []
    for row in rows:
        tokens = extract_tokens(row.get("raw_text", ""), stopwords, args.min_token_length)
        for token in dict.fromkeys(tokens):
            events.append(
                {
                    "half": row.get("half", ""),
                    "timestamp_sec": row.get("timestamp_sec", ""),
                    "end_timestamp_sec": row.get("timestamp_sec", ""),
                    "event_type": "text_cue",
                    "cue_text": token,
                    "evidence_count": "1",
                    "raw_text": row.get("raw_text", ""),
                    "source_image": row.get("source_image", ""),
                }
            )

    merged = merge_events(events, merge_gap_sec=args.merge_gap_sec)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "half",
        "timestamp_sec",
        "end_timestamp_sec",
        "event_type",
        "cue_text",
        "evidence_count",
        "raw_text",
        "source_image",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(merged)

    print(f"input rows: {len(rows)}")
    print(f"text cue events: {len(merged)}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
