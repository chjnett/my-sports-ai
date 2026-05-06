"""Summarize YOLO detection CSV outputs."""

from __future__ import annotations

import argparse
import csv
from collections import Counter, defaultdict
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize broadcast graphics detection CSV.")
    parser.add_argument("--input", required=True, type=Path, help="Detection CSV path.")
    parser.add_argument("--thresholds", nargs="*", type=float, default=[0.25, 0.5, 0.7, 0.85])
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"CSV not found: {args.input}")

    rows: list[dict[str, str]] = []
    with args.input.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)

    print(f"csv: {args.input}")
    print(f"detections: {len(rows)}")
    if not rows:
        return

    by_class = Counter(row["class_name"] for row in rows)
    print("class counts:")
    for class_name, count in by_class.most_common():
        print(f"  {class_name}: {count}")

    confidence_by_class: dict[str, list[float]] = defaultdict(list)
    frames_by_class: dict[str, set[str]] = defaultdict(set)
    halves = Counter()
    for row in rows:
        class_name = row["class_name"]
        confidence = float(row["confidence"])
        confidence_by_class[class_name].append(confidence)
        frames_by_class[class_name].add(row["image_path"])
        halves[row["half"]] += 1

    print("half counts:")
    for half, count in sorted(halves.items()):
        print(f"  half {half}: {count}")

    print("confidence summary:")
    for class_name, values in sorted(confidence_by_class.items()):
        values = sorted(values)
        avg = sum(values) / len(values)
        print(
            f"  {class_name}: "
            f"min={values[0]:.3f}, avg={avg:.3f}, max={values[-1]:.3f}, "
            f"unique_frames={len(frames_by_class[class_name])}"
        )
        for threshold in args.thresholds:
            count = sum(value >= threshold for value in values)
            print(f"    >= {threshold:.2f}: {count}")

    print("low confidence examples:")
    for row in sorted(rows, key=lambda item: float(item["confidence"]))[:10]:
        print(
            f"  conf={float(row['confidence']):.3f} "
            f"half={row['half']} t={row['timestamp_sec']} "
            f"class={row['class_name']} path={row['image_path']}"
        )


if __name__ == "__main__":
    main()
