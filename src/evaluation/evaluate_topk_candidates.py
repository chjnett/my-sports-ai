"""Evaluate Recall@tolerance for ranked highlight candidate Top-K slices."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate ranked candidate Top-K recall.")
    parser.add_argument("--labels", required=True, type=Path, help="Goal label CSV.")
    parser.add_argument("--candidates", required=True, type=Path, help="Ranked candidate CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Top-K summary CSV.")
    parser.add_argument("--details-output", type=Path, help="Optional per-goal Top-K details CSV.")
    parser.add_argument("--top-k", default="3,5,10,20", help="Comma-separated K values.")
    parser.add_argument("--tolerances", default="5,10,30", help="Comma-separated tolerance seconds.")
    return parser.parse_args()


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_ints(raw: str) -> list[int]:
    values = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if not values:
        raise ValueError("At least one integer value is required.")
    return sorted(set(values))


def parse_floats(raw: str) -> list[float]:
    values = [float(part.strip()) for part in raw.split(",") if part.strip()]
    if not values:
        raise ValueError("At least one tolerance value is required.")
    return sorted(set(values))


def load_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"CSV not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def goal_second(row: dict[str, str]) -> float:
    if row.get("half_second"):
        return parse_float(row.get("half_second"))
    return parse_float(row.get("timestamp_sec"))


def event_second(row: dict[str, str]) -> float:
    return parse_float(row.get("timestamp_sec"))


def nearest_event(goal: dict[str, str], candidates: list[dict[str, str]]) -> tuple[dict[str, str] | None, float | None]:
    goal_half = str(goal.get("half", "")).strip()
    goal_ts = goal_second(goal)
    same_half = [candidate for candidate in candidates if str(candidate.get("half", "")).strip() == goal_half]
    if not same_half:
        return None, None
    nearest = min(same_half, key=lambda candidate: abs(event_second(candidate) - goal_ts))
    return nearest, abs(event_second(nearest) - goal_ts)


def main() -> None:
    args = parse_args()
    top_k_values = parse_ints(args.top_k)
    tolerances = parse_floats(args.tolerances)
    goals = [row for row in load_csv(args.labels) if row.get("label") == "Goal"]
    candidates = sorted(load_csv(args.candidates), key=lambda row: int(row.get("rank", "999999")))

    summary_rows: list[dict[str, str]] = []
    detail_rows: list[dict[str, str]] = []

    for top_k in top_k_values:
        selected = candidates[:top_k]
        hit_counts = {tolerance: 0 for tolerance in tolerances}

        for goal in goals:
            nearest, delta = nearest_event(goal, selected)
            detail = {
                "top_k": str(top_k),
                "goal_half": goal.get("half", ""),
                "goal_second": f"{goal_second(goal):.1f}",
                "goal_game_time": goal.get("game_time", ""),
                "nearest_rank": "",
                "nearest_candidate_id": "",
                "nearest_timestamp_sec": "",
                "nearest_delta_sec": "",
                "nearest_rank_score": "",
                "nearest_evidence_types": "",
                "nearest_cue_texts": "",
            }
            if nearest is not None and delta is not None:
                detail.update(
                    {
                        "nearest_rank": nearest.get("rank", ""),
                        "nearest_candidate_id": nearest.get("candidate_id", ""),
                        "nearest_timestamp_sec": f"{event_second(nearest):.1f}",
                        "nearest_delta_sec": f"{delta:.1f}",
                        "nearest_rank_score": nearest.get("rank_score", ""),
                        "nearest_evidence_types": nearest.get("evidence_types", ""),
                        "nearest_cue_texts": nearest.get("cue_texts", ""),
                    }
                )
            for tolerance in tolerances:
                hit = delta is not None and delta <= tolerance
                detail[f"hit_at_{int(tolerance)}s"] = "1" if hit else "0"
                if hit:
                    hit_counts[tolerance] += 1
            detail_rows.append(detail)

        summary = {
            "top_k": str(top_k),
            "candidate_count": str(len(selected)),
            "goal_count": str(len(goals)),
        }
        for tolerance in tolerances:
            hits = hit_counts[tolerance]
            recall = hits / len(goals) if goals else 0.0
            summary[f"hits_at_{int(tolerance)}s"] = str(hits)
            summary[f"recall_at_{int(tolerance)}s"] = f"{recall:.3f}"
        summary_rows.append(summary)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        fieldnames = list(summary_rows[0].keys()) if summary_rows else []
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(summary_rows)

    if args.details_output:
        args.details_output.parent.mkdir(parents=True, exist_ok=True)
        with args.details_output.open("w", newline="", encoding="utf-8") as handle:
            fieldnames = list(detail_rows[0].keys()) if detail_rows else []
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(detail_rows)

    print(f"goals: {len(goals)}")
    print(f"candidates: {len(candidates)}")
    for row in summary_rows:
        print(row)
    print(f"output: {args.output}")
    if args.details_output:
        print(f"details output: {args.details_output}")


if __name__ == "__main__":
    main()
