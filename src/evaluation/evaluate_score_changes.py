"""Evaluate OCR score-change events against SoccerNet Goal labels."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compare detected events to SoccerNet Goal labels.")
    parser.add_argument("--labels", required=True, type=Path, help="Label CSV from src.data.labels or phase1a.")
    parser.add_argument("--score-events", required=True, type=Path, help="Detected event CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Per-goal evaluation CSV.")
    parser.add_argument("--tolerances", default="5,10,30", help="Comma-separated tolerance seconds.")
    parser.add_argument(
        "--event-types",
        default="score_change",
        help="Comma-separated event types to evaluate. Use 'all' for every row.",
    )
    return parser.parse_args()


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_tolerances(raw: str) -> list[float]:
    tolerances: list[float] = []
    for part in raw.split(","):
        text = part.strip()
        if not text:
            continue
        tolerances.append(float(text))
    if not tolerances:
        raise ValueError("At least one tolerance is required.")
    return sorted(tolerances)


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"CSV not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_event_types(raw: str) -> set[str] | None:
    if raw.strip().lower() == "all":
        return None
    return {item.strip() for item in raw.split(",") if item.strip()}


def goal_second(row: dict[str, str]) -> float:
    if row.get("half_second"):
        return parse_float(row.get("half_second"))
    if row.get("timestamp_sec"):
        return parse_float(row.get("timestamp_sec"))
    return 0.0


def event_second(row: dict[str, str]) -> float:
    return parse_float(row.get("timestamp_sec"))


def best_match(goal: dict[str, str], events: list[dict[str, str]]) -> tuple[dict[str, str] | None, float | None]:
    goal_half = str(goal.get("half", "")).strip()
    goal_ts = goal_second(goal)
    candidates = [event for event in events if str(event.get("half", "")).strip() == goal_half]
    if not candidates:
        return None, None
    nearest = min(candidates, key=lambda event: abs(event_second(event) - goal_ts))
    return nearest, abs(event_second(nearest) - goal_ts)


def main() -> None:
    args = parse_args()
    tolerances = parse_tolerances(args.tolerances)
    event_types = parse_event_types(args.event_types)
    goals = [row for row in load_csv(args.labels) if row.get("label") == "Goal"]
    events = [
        row
        for row in load_csv(args.score_events)
        if event_types is None or row.get("event_type") in event_types
    ]

    fieldnames = [
        "goal_half",
        "goal_second",
        "goal_game_time",
        "goal_team",
        "nearest_score_event_second",
        "nearest_delta_sec",
        "nearest_event_type",
        "nearest_evidence_types",
        "nearest_cue_texts",
        "nearest_from_score",
        "nearest_to_score",
        *[f"hit_at_{int(tolerance)}s" for tolerance in tolerances],
    ]

    output_rows: list[dict[str, str]] = []
    hit_counts = {tolerance: 0 for tolerance in tolerances}

    for goal in goals:
        nearest, delta = best_match(goal, events)
        output = {
            "goal_half": goal.get("half", ""),
            "goal_second": f"{goal_second(goal):.1f}",
            "goal_game_time": goal.get("game_time", ""),
            "goal_team": goal.get("team", ""),
            "nearest_score_event_second": "",
            "nearest_delta_sec": "",
            "nearest_event_type": "",
            "nearest_evidence_types": "",
            "nearest_cue_texts": "",
            "nearest_from_score": "",
            "nearest_to_score": "",
        }
        if nearest is not None and delta is not None:
            output.update(
                {
                    "nearest_score_event_second": f"{event_second(nearest):.1f}",
                    "nearest_delta_sec": f"{delta:.1f}",
                    "nearest_event_type": nearest.get("event_type", ""),
                    "nearest_evidence_types": nearest.get("evidence_types", ""),
                    "nearest_cue_texts": nearest.get("cue_texts", ""),
                    "nearest_from_score": nearest.get("from_score", ""),
                    "nearest_to_score": nearest.get("to_score", "") or nearest.get("score_signal", ""),
                }
            )
        for tolerance in tolerances:
            hit = delta is not None and delta <= tolerance
            output[f"hit_at_{int(tolerance)}s"] = "1" if hit else "0"
            if hit:
                hit_counts[tolerance] += 1
        output_rows.append(output)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_rows)

    goal_count = len(goals)
    print(f"goals: {goal_count}")
    print(f"events: {len(events)}")
    for tolerance in tolerances:
        recall = hit_counts[tolerance] / goal_count if goal_count else 0.0
        print(f"Recall@{int(tolerance)}s: {hit_counts[tolerance]}/{goal_count} = {recall:.3f}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
