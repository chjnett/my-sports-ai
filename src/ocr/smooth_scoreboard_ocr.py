"""Smooth scoreboard OCR rows and extract score-change events."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, deque
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Score:
    home: int
    away: int

    @property
    def text(self) -> str:
        return f"{self.home}-{self.away}"


@dataclass(frozen=True)
class Evidence:
    timestamp_sec: float
    score: Score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Smooth scoreboard OCR score readings.")
    parser.add_argument("--ocr", required=True, type=Path, help="Raw OCR CSV from run_scoreboard_ocr.py.")
    parser.add_argument("--output", required=True, type=Path, help="Smoothed per-row CSV output.")
    parser.add_argument("--events-output", type=Path, help="Score-change event CSV output.")
    parser.add_argument("--window-sec", type=float, default=8.0, help="Recent OCR window used for voting.")
    parser.add_argument("--min-votes", type=int, default=3, help="Minimum repeated OCR votes to accept a score.")
    parser.add_argument(
        "--max-score-step",
        type=int,
        default=1,
        help="Maximum total score increase accepted in one transition.",
    )
    return parser.parse_args()


def parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_score(row: dict[str, str]) -> Score | None:
    home = parse_int(row.get("parsed_home_score"))
    away = parse_int(row.get("parsed_away_score"))
    if home is None or away is None:
        return None
    if home < 0 or away < 0:
        return None
    return Score(home=home, away=away)


def parse_clock_sec(value: str | None) -> int | None:
    if not value:
        return None
    parts = str(value).split(":")
    if len(parts) != 2:
        return None
    minute = parse_int(parts[0])
    second = parse_int(parts[1])
    if minute is None or second is None or second >= 60:
        return None
    return minute * 60 + second


def score_delta(previous: Score, current: Score) -> tuple[int, int]:
    return current.home - previous.home, current.away - previous.away


def is_valid_forward_change(previous: Score, current: Score, max_score_step: int) -> bool:
    home_delta, away_delta = score_delta(previous, current)
    total_delta = home_delta + away_delta
    return home_delta >= 0 and away_delta >= 0 and 1 <= total_delta <= max_score_step


def choose_score(window: deque[Evidence], min_votes: int) -> tuple[Score | None, int]:
    counts = Counter(item.score for item in window)
    if not counts:
        return None, 0
    score, votes = counts.most_common(1)[0]
    if votes < min_votes:
        return None, votes
    return score, votes


def smooth_half(
    rows: list[dict[str, str]],
    window_sec: float,
    min_votes: int,
    max_score_step: int,
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    rows = sorted(rows, key=lambda row: parse_float(row.get("timestamp_sec")))
    evidence_window: deque[Evidence] = deque()
    stable_score: Score | None = None
    output_rows: list[dict[str, str]] = []
    event_rows: list[dict[str, str]] = []

    for row in rows:
        timestamp = parse_float(row.get("timestamp_sec"))
        observed_score = parse_score(row)
        if observed_score is not None:
            evidence_window.append(Evidence(timestamp_sec=timestamp, score=observed_score))

        while evidence_window and evidence_window[0].timestamp_sec < timestamp - window_sec:
            evidence_window.popleft()

        candidate, votes = choose_score(evidence_window, min_votes=min_votes)
        changed = False
        state = "no_candidate"

        if stable_score is None and candidate is not None:
            stable_score = candidate
            state = "initialized"
        elif candidate is None:
            state = "held"
        elif stable_score == candidate:
            state = "confirmed"
        elif stable_score is not None and is_valid_forward_change(stable_score, candidate, max_score_step):
            previous_score = stable_score
            stable_score = candidate
            changed = True
            state = "score_changed"
            home_delta, away_delta = score_delta(previous_score, candidate)
            scoring_side = "home" if home_delta > away_delta else "away"
            event_rows.append(
                {
                    "half": row.get("half", ""),
                    "timestamp_sec": f"{timestamp:.1f}",
                    "event_type": "score_change",
                    "from_score": previous_score.text,
                    "to_score": candidate.text,
                    "home_delta": home_delta,
                    "away_delta": away_delta,
                    "scoring_side": scoring_side,
                    "evidence_votes": votes,
                    "evidence_window_sec": window_sec,
                    "raw_text": row.get("raw_text", ""),
                    "source_image": row.get("source_image", ""),
                }
            )
        else:
            state = "rejected_candidate"

        stable_home = "" if stable_score is None else str(stable_score.home)
        stable_away = "" if stable_score is None else str(stable_score.away)
        stable_text = "" if stable_score is None else stable_score.text
        clock_sec = parse_clock_sec(row.get("parsed_clock"))

        output = dict(row)
        output.update(
            {
                "observed_score": "" if observed_score is None else observed_score.text,
                "stable_home_score": stable_home,
                "stable_away_score": stable_away,
                "stable_score": stable_text,
                "score_state": state,
                "score_changed": "1" if changed else "0",
                "score_candidate_votes": votes,
                "parsed_clock_sec": "" if clock_sec is None else str(clock_sec),
            }
        )
        output_rows.append(output)

    return output_rows, event_rows


def main() -> None:
    args = parse_args()
    if not args.ocr.exists():
        raise SystemExit(f"OCR CSV not found: {args.ocr}")

    with args.ocr.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        input_fieldnames = list(reader.fieldnames or [])

    rows_by_half: dict[str, list[dict[str, str]]] = {}
    for row in rows:
        rows_by_half.setdefault(row.get("half", ""), []).append(row)

    smoothed_rows: list[dict[str, str]] = []
    event_rows: list[dict[str, str]] = []
    for half in sorted(rows_by_half, key=lambda value: int(value) if str(value).isdigit() else 99):
        half_rows, half_events = smooth_half(
            rows_by_half[half],
            window_sec=args.window_sec,
            min_votes=args.min_votes,
            max_score_step=args.max_score_step,
        )
        smoothed_rows.extend(half_rows)
        event_rows.extend(half_events)

    extra_fieldnames = [
        "observed_score",
        "stable_home_score",
        "stable_away_score",
        "stable_score",
        "score_state",
        "score_changed",
        "score_candidate_votes",
        "parsed_clock_sec",
    ]
    output_fieldnames = input_fieldnames + [name for name in extra_fieldnames if name not in input_fieldnames]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(smoothed_rows)

    if args.events_output:
        args.events_output.parent.mkdir(parents=True, exist_ok=True)
        event_fieldnames = [
            "half",
            "timestamp_sec",
            "event_type",
            "from_score",
            "to_score",
            "home_delta",
            "away_delta",
            "scoring_side",
            "evidence_votes",
            "evidence_window_sec",
            "raw_text",
            "source_image",
        ]
        with args.events_output.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=event_fieldnames)
            writer.writeheader()
            writer.writerows(event_rows)

    print(f"input rows: {len(rows)}")
    print(f"smoothed rows: {len(smoothed_rows)}")
    print(f"score-change events: {len(event_rows)}")
    print(f"output: {args.output}")
    if args.events_output:
        print(f"events output: {args.events_output}")


if __name__ == "__main__":
    main()
