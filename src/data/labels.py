from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_TARGET_LABELS = {
    "Goal",
    "Yellow card",
    "Red card",
    "Substitution",
}

GAME_TIME_RE = re.compile(r"^\s*(?P<half>\d+)\s*-\s*(?P<minute>\d+):(?P<second>\d+)\s*$")


@dataclass(frozen=True)
class SoccerNetEvent:
    match_id: str
    label_path: str
    half: int
    half_second: int
    match_second: int
    position_ms: int | None
    label: str
    team: str
    visibility: str
    game_time: str


def normalize_match_id(label_path: Path, data_root: Path) -> str:
    match_dir = label_path.parent
    try:
        return match_dir.relative_to(data_root).as_posix()
    except ValueError:
        return match_dir.as_posix()


def parse_game_time(game_time: str) -> tuple[int, int, int]:
    match = GAME_TIME_RE.match(game_time)
    if not match:
        raise ValueError(f"Invalid SoccerNet gameTime value: {game_time!r}")

    half = int(match.group("half"))
    minute = int(match.group("minute"))
    second = int(match.group("second"))
    half_second = minute * 60 + second

    # SoccerNet stores each half as a separate video. This timeline offset is
    # useful for whole-match reports, while half_second stays aligned to video time.
    match_second = half_second if half == 1 else 45 * 60 + half_second
    return half, half_second, match_second


def parse_position_ms(value: object) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def load_events(
    label_path: str | Path,
    data_root: str | Path = "data/spotting",
    target_labels: set[str] | None = None,
) -> list[SoccerNetEvent]:
    label_file = Path(label_path)
    root = Path(data_root)
    targets = target_labels or DEFAULT_TARGET_LABELS

    with label_file.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    match_id = normalize_match_id(label_file, root)
    events: list[SoccerNetEvent] = []

    for annotation in payload.get("annotations", []):
        label = str(annotation.get("label", "")).strip()
        if targets and label not in targets:
            continue

        game_time = str(annotation.get("gameTime", "")).strip()
        half, half_second, match_second = parse_game_time(game_time)

        events.append(
            SoccerNetEvent(
                match_id=match_id,
                label_path=label_file.as_posix(),
                half=half,
                half_second=half_second,
                match_second=match_second,
                position_ms=parse_position_ms(annotation.get("position")),
                label=label,
                team=str(annotation.get("team", "")),
                visibility=str(annotation.get("visibility", "")),
                game_time=game_time,
            )
        )

    return events


def iter_label_files(data_root: str | Path) -> Iterable[Path]:
    yield from Path(data_root).rglob("Labels-v2.json")


def load_events_from_root(
    data_root: str | Path = "data/spotting",
    target_labels: set[str] | None = None,
) -> list[SoccerNetEvent]:
    events: list[SoccerNetEvent] = []
    for label_file in iter_label_files(data_root):
        events.extend(load_events(label_file, data_root=data_root, target_labels=target_labels))
    return events


def write_events_csv(events: Iterable[SoccerNetEvent], output_path: str | Path) -> Path:
    rows = [asdict(event) for event in events]
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "match_id",
        "label_path",
        "half",
        "half_second",
        "match_second",
        "position_ms",
        "label",
        "team",
        "visibility",
        "game_time",
    ]

    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    return out


def parse_label_filter(raw_labels: str | None) -> set[str] | None:
    if not raw_labels:
        return DEFAULT_TARGET_LABELS
    if raw_labels.lower() == "all":
        return None
    return {label.strip() for label in raw_labels.split(",") if label.strip()}


def main() -> None:
    parser = argparse.ArgumentParser(description="Parse SoccerNet Labels-v2.json files.")
    parser.add_argument("--data-root", default="data/spotting", help="Root containing SoccerNet match folders.")
    parser.add_argument("--label-file", help="Specific Labels-v2.json file to parse.")
    parser.add_argument("--labels", help="Comma-separated labels to keep. Use 'all' for every label.")
    parser.add_argument("--output", default="outputs/reports/labels_events.csv", help="CSV output path.")
    args = parser.parse_args()

    target_labels = parse_label_filter(args.labels)
    if args.label_file:
        events = load_events(args.label_file, data_root=args.data_root, target_labels=target_labels)
    else:
        events = load_events_from_root(args.data_root, target_labels=target_labels)

    output = write_events_csv(events, args.output)
    print(f"Wrote {len(events)} events to {output}")


if __name__ == "__main__":
    main()
