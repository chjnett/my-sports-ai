"""Render frame strips for event segment CSV rows."""

from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render contact sheets around replay segment events.")
    parser.add_argument("--events", required=True, type=Path, help="Replay event CSV path.")
    parser.add_argument("--frames-root", required=True, type=Path, help="Root containing half_* frame folders.")
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--event-type", default="replay_segment")
    parser.add_argument("--sample-every-sec", type=int, default=5)
    parser.add_argument("--padding-sec", type=int, default=0)
    parser.add_argument("--thumb-width", type=int, default=320)
    return parser.parse_args()


def frame_path(frames_root: Path, half: str, timestamp_sec: float) -> Path:
    timestamp_ms = int(round(timestamp_sec * 1000))
    return frames_root / f"half_{half}" / f"{timestamp_ms:010d}.jpg"


def read_events(path: Path, event_type: str) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return [row for row in reader if row["event_type"] == event_type]


def add_label(image: np.ndarray, text: str) -> np.ndarray:
    output = image.copy()
    cv2.rectangle(output, (0, 0), (output.shape[1], 34), (0, 0, 0), -1)
    cv2.putText(output, text, (8, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 255, 0), 2, cv2.LINE_AA)
    return output


def make_sheet(images: list[np.ndarray], thumb_width: int) -> np.ndarray | None:
    if not images:
        return None
    thumbs = []
    for image in images:
        h, w = image.shape[:2]
        scale = thumb_width / max(w, 1)
        thumbs.append(cv2.resize(image, (thumb_width, int(h * scale))))
    thumb_h = max(thumb.shape[0] for thumb in thumbs)
    cols = min(5, len(thumbs))
    rows = math.ceil(len(thumbs) / cols)
    sheet = np.zeros((rows * thumb_h, cols * thumb_width, 3), dtype=np.uint8)
    for index, thumb in enumerate(thumbs):
        row = index // cols
        col = index % cols
        y = row * thumb_h
        x = col * thumb_width
        sheet[y : y + thumb.shape[0], x : x + thumb.shape[1]] = thumb
    return sheet


def main() -> None:
    args = parse_args()
    if not args.events.exists():
        raise SystemExit(f"Events CSV not found: {args.events}")
    if not args.frames_root.exists():
        raise SystemExit(f"Frames root not found: {args.frames_root}")

    events = read_events(args.events, args.event_type)
    args.output_root.mkdir(parents=True, exist_ok=True)
    written = 0
    missing_frames = 0

    for index, event in enumerate(events, start=1):
        half = event["half"]
        start_sec = float(event["start_sec"]) - args.padding_sec
        end_sec = float(event["end_sec"]) + args.padding_sec
        timestamps = list(range(max(0, math.floor(start_sec)), math.ceil(end_sec) + 1, args.sample_every_sec))
        if timestamps and timestamps[-1] != round(end_sec):
            timestamps.append(math.ceil(end_sec))

        images: list[np.ndarray] = []
        for timestamp in timestamps:
            path = frame_path(args.frames_root, half, float(timestamp))
            image = cv2.imread(str(path))
            if image is None:
                missing_frames += 1
                continue
            images.append(add_label(image, f"half {half}  t={timestamp}s"))

        sheet = make_sheet(images, args.thumb_width)
        if sheet is None:
            continue
        duration = float(event["duration_sec"])
        output = args.output_root / f"{index:03d}__half_{half}__{event['start_sec']}-{event['end_sec']}s__dur_{duration:.1f}.jpg"
        cv2.imwrite(str(output), sheet)
        written += 1

    print(f"events: {args.events}")
    print(f"segments selected: {len(events)}")
    print(f"segment sheets written: {written}")
    print(f"missing frames: {missing_frames}")
    print(f"output: {args.output_root}")


if __name__ == "__main__":
    main()
