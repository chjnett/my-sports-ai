"""Crop detected regions from frames using a detection CSV."""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from pathlib import Path

import cv2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Crop detection boxes into OCR-ready image folders.")
    parser.add_argument("--detections", required=True, type=Path, help="Detection CSV path.")
    parser.add_argument("--output-root", required=True, type=Path, help="Crop output root.")
    parser.add_argument("--summary", default=Path("outputs/reports/detection_crop_summary.csv"), type=Path)
    parser.add_argument("--class-name", default="scoreboard")
    parser.add_argument("--min-conf", type=float, default=0.70)
    parser.add_argument("--padding", type=int, default=8)
    parser.add_argument("--scale-factor", type=float, default=1.0, help="Upscale crop before saving (e.g. 2.0 for 2x size)")
    parser.add_argument(
        "--best-per-frame",
        action="store_true",
        help="Keep only the highest-confidence detection per image.",
    )
    parser.add_argument("--limit", type=int, default=0)
    return parser.parse_args()


def load_rows(path: Path, class_name: str, min_conf: float) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = [
            row
            for row in reader
            if row["class_name"] == class_name and float(row["confidence"]) >= min_conf
        ]
    return rows


def keep_best_per_frame(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["image_path"]].append(row)
    return [
        max(image_rows, key=lambda row: float(row["confidence"]))
        for image_rows in grouped.values()
    ]


def crop_row(row: dict[str, str], output_root: Path, padding: int, scale_factor: float) -> dict[str, str] | None:
    image_path = Path(row["image_path"])
    image = cv2.imread(str(image_path))
    if image is None:
        return None

    height, width = image.shape[:2]
    x1 = max(0, int(round(float(row["x1"]))) - padding)
    y1 = max(0, int(round(float(row["y1"]))) - padding)
    x2 = min(width - 1, int(round(float(row["x2"]))) + padding)
    y2 = min(height - 1, int(round(float(row["y2"]))) + padding)
    if x2 <= x1 or y2 <= y1:
        return None

    crop = image[y1:y2, x1:x2]
    if scale_factor != 1.0:
        crop = cv2.resize(crop, None, fx=scale_factor, fy=scale_factor, interpolation=cv2.INTER_CUBIC)

    half = str(row["half"])
    timestamp = str(row["timestamp_sec"]).replace(".", "p")
    class_name = row["class_name"]
    output_dir = output_root / class_name / f"half_{half}"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{timestamp}s__conf_{float(row['confidence']):.3f}.jpg"
    cv2.imwrite(str(output_path), crop)

    return {
        "class_name": class_name,
        "half": half,
        "timestamp_sec": row["timestamp_sec"],
        "confidence": row["confidence"],
        "x1": str(x1),
        "y1": str(y1),
        "x2": str(x2),
        "y2": str(y2),
        "source_image": image_path.as_posix(),
        "crop_image": output_path.as_posix(),
    }


def write_summary(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "class_name",
        "half",
        "timestamp_sec",
        "confidence",
        "x1",
        "y1",
        "x2",
        "y2",
        "source_image",
        "crop_image",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    args = parse_args()
    if not args.detections.exists():
        raise SystemExit(f"Detections CSV not found: {args.detections}")

    rows = load_rows(args.detections, args.class_name, args.min_conf)
    if args.best_per_frame:
        rows = keep_best_per_frame(rows)
    rows = sorted(rows, key=lambda row: (int(float(row["half"])), float(row["timestamp_sec"])))
    if args.limit > 0:
        rows = rows[: args.limit]

    summary_rows: list[dict[str, str]] = []
    skipped = 0
    for row in rows:
        summary = crop_row(row, args.output_root, args.padding, args.scale_factor)
        if summary is None:
            skipped += 1
            continue
        summary_rows.append(summary)

    write_summary(args.summary, summary_rows)
    print(f"detections: {args.detections}")
    print(f"class: {args.class_name}")
    print(f"rows selected: {len(rows)}")
    print(f"crops written: {len(summary_rows)}")
    print(f"skipped: {skipped}")
    print(f"output root: {args.output_root}")
    print(f"summary: {args.summary}")


if __name__ == "__main__":
    main()
