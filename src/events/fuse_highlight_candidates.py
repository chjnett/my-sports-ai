"""Fuse multiple event signals into highlight candidates."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fuse score/text/replay events into highlight candidates.")
    parser.add_argument("--score-events", type=Path, help="Score-change event CSV.")
    parser.add_argument("--text-events", type=Path, help="Text cue event CSV.")
    parser.add_argument("--replay-events", type=Path, help="Replay event CSV.")
    parser.add_argument("--label-events", type=Path, help="Optional SoccerNet label event CSV.")
    parser.add_argument(
        "--label-kinds",
        default="Yellow card,Red card,Substitution",
        help="Comma-separated SoccerNet labels to include as fallback highlight candidates.",
    )
    parser.add_argument("--output", required=True, type=Path, help="Output fused candidate CSV.")
    parser.add_argument("--merge-window-sec", type=float, default=30.0)
    return parser.parse_args()


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def load_csv(path: Path | None) -> list[dict[str, str]]:
    if path is None:
        return []
    if not path.exists():
        raise SystemExit(f"CSV not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def normalize_label_name(raw: str) -> str:
    return str(raw or "").strip().lower().replace(" ", "_")


def parse_label_kinds(raw: str) -> set[str]:
    return {label.strip() for label in raw.split(",") if label.strip()}


def normalize_event(row: dict[str, str], source: str) -> dict[str, str]:
    if source == "label":
        label = row.get("label", "label_event")
        event_type = normalize_label_name(label)
        timestamp = row.get("half_second") or row.get("timestamp_sec") or "0"
        text = f"{label}:{row.get('team', '')}".strip(":")
    else:
        event_type = row.get("event_type", source)
        timestamp = row.get("timestamp_sec") or row.get("start_sec") or "0"
        text = row.get("cue_text") or row.get("to_score") or row.get("raw_text") or event_type
    return {
        "half": row.get("half", ""),
        "timestamp_sec": timestamp,
        "event_type": event_type,
        "source": source,
        "text": text,
        "raw_text": row.get("raw_text", ""),
        "source_image": row.get("source_image", ""),
    }


def can_merge(candidate: dict[str, str], event: dict[str, str], merge_window_sec: float) -> bool:
    if candidate["half"] != event["half"]:
        return False
    start = parse_float(candidate["start_timestamp_sec"])
    end = parse_float(candidate["end_timestamp_sec"])
    ts = parse_float(event["timestamp_sec"])
    return start - merge_window_sec <= ts <= end + merge_window_sec


def update_candidate(candidate: dict[str, str], event: dict[str, str]) -> None:
    ts = parse_float(event["timestamp_sec"])
    start = parse_float(candidate["start_timestamp_sec"])
    end = parse_float(candidate["end_timestamp_sec"])
    candidate["start_timestamp_sec"] = f"{min(start, ts):.1f}"
    candidate["end_timestamp_sec"] = f"{max(end, ts):.1f}"

    evidence_types = set(filter(None, candidate["evidence_types"].split(";")))
    evidence_types.add(event["event_type"])
    candidate["evidence_types"] = ";".join(sorted(evidence_types))
    candidate["evidence_count"] = str(int(candidate["evidence_count"]) + 1)

    if event["source"] == "text" and event["text"]:
        cue_texts = set(filter(None, candidate["cue_texts"].split(";")))
        cue_texts.add(event["text"])
        candidate["cue_texts"] = ";".join(sorted(cue_texts))

    if event["source"] == "label" and event["text"]:
        cue_texts = set(filter(None, candidate["cue_texts"].split(";")))
        cue_texts.add(event["text"])
        candidate["cue_texts"] = ";".join(sorted(cue_texts))

    if event["source"] == "score":
        candidate["score_signal"] = event["text"]
        candidate["timestamp_sec"] = f"{parse_float(event['timestamp_sec']):.1f}"
    elif not candidate["score_signal"]:
        candidate["timestamp_sec"] = candidate["start_timestamp_sec"]
    if not candidate["example_raw_text"] and event["raw_text"]:
        candidate["example_raw_text"] = event["raw_text"]
    if not candidate["source_image"] and event["source_image"]:
        candidate["source_image"] = event["source_image"]


def make_candidate(event: dict[str, str], index: int) -> dict[str, str]:
    ts = parse_float(event["timestamp_sec"])
    candidate = {
        "candidate_id": f"candidate_{index:04d}",
        "half": event["half"],
        "timestamp_sec": f"{ts:.1f}",
        "start_timestamp_sec": f"{ts:.1f}",
        "end_timestamp_sec": f"{ts:.1f}",
        "event_type": "highlight_candidate",
        "evidence_types": event["event_type"],
        "evidence_count": "0",
        "score_signal": "",
        "cue_texts": "",
        "example_raw_text": "",
        "source_image": "",
    }
    update_candidate(candidate, event)
    return candidate


def main() -> None:
    args = parse_args()
    events: list[dict[str, str]] = []
    events.extend(normalize_event(row, "score") for row in load_csv(args.score_events))
    events.extend(normalize_event(row, "text") for row in load_csv(args.text_events))
    replay_rows = [
        row
        for row in load_csv(args.replay_events)
        if row.get("event_type") in {"replay_transition_logo", "replay_segment"}
    ]
    events.extend(normalize_event(row, "replay") for row in replay_rows)
    label_kinds = parse_label_kinds(args.label_kinds)
    label_rows = [row for row in load_csv(args.label_events) if row.get("label") in label_kinds]
    events.extend(normalize_event(row, "label") for row in label_rows)
    events.sort(key=lambda row: (row.get("half", ""), parse_float(row.get("timestamp_sec"))))

    candidates: list[dict[str, str]] = []
    for event in events:
        for candidate in candidates:
            if can_merge(candidate, event, args.merge_window_sec):
                update_candidate(candidate, event)
                break
        else:
            candidates.append(make_candidate(event, len(candidates) + 1))

    args.output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "candidate_id",
        "half",
        "timestamp_sec",
        "start_timestamp_sec",
        "end_timestamp_sec",
        "event_type",
        "evidence_types",
        "evidence_count",
        "score_signal",
        "cue_texts",
        "example_raw_text",
        "source_image",
    ]
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(candidates)

    print(f"input events: {len(events)}")
    print(f"highlight candidates: {len(candidates)}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
