"""Render detection CSV rows as review images."""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

import cv2
import numpy as np


COLORS = {
    "scoreboard": (0, 255, 255),
    "overlay": (255, 0, 255),
    "replay_logo": (0, 255, 0),
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Draw detection boxes from CSV for visual review.")
    parser.add_argument("--detections", required=True, type=Path, help="Detection CSV path.")
    parser.add_argument("--output-root", required=True, type=Path, help="Output review directory.")
    parser.add_argument("--class-name", default="", help="Optional class filter.")
    parser.add_argument("--min-conf", type=float, default=0.0)
    parser.add_argument("--top-k", type=int, default=0, help="Keep top K rows by confidence. 0 keeps all.")
    parser.add_argument("--contact-sheet-cols", type=int, default=4)
    parser.add_argument("--contact-sheet-thumb-width", type=int, default=360)
    return parser.parse_args()


def load_rows(path: Path, class_name: str, min_conf: float) -> list[dict[str, str]]:
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for row in reader:
            if class_name and row["class_name"] != class_name:
                continue
            if float(row["confidence"]) < min_conf:
                continue
            rows.append(row)
    return rows


def group_by_image(rows: list[dict[str, str]]) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        grouped[row["image_path"]].append(row)
    return dict(grouped)


def draw_rows(image_path: Path, rows: list[dict[str, str]]) -> np.ndarray | None:
    image = cv2.imread(str(image_path))
    if image is None:
        return None

    for row in rows:
        class_name = row["class_name"]
        color = COLORS.get(class_name, (255, 255, 255))
        x1 = int(round(float(row["x1"])))
        y1 = int(round(float(row["y1"])))
        x2 = int(round(float(row["x2"])))
        y2 = int(round(float(row["y2"])))
        confidence = float(row["confidence"])
        cv2.rectangle(image, (x1, y1), (x2, y2), color, 2)
        label = f"{class_name} {confidence:.3f} h{row['half']} t={row['timestamp_sec']}"
        cv2.putText(
            image,
            label,
            (x1, max(22, y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            color,
            2,
            cv2.LINE_AA,
        )
    return image


def safe_name(index: int, rows: list[dict[str, str]]) -> str:
    first = rows[0]
    class_names = "_".join(sorted({row["class_name"] for row in rows}))
    conf = max(float(row["confidence"]) for row in rows)
    timestamp = str(first["timestamp_sec"]).replace(".", "p")
    return f"{index:04d}__{class_names}__h{first['half']}__{timestamp}s__conf_{conf:.3f}.jpg"


def write_contact_sheet(review_paths: list[Path], output: Path, cols: int, thumb_width: int) -> None:
    thumbs: list[np.ndarray] = []
    for path in review_paths:
        image = cv2.imread(str(path))
        if image is None:
            continue
        h, w = image.shape[:2]
        scale = thumb_width / max(w, 1)
        thumbs.append(cv2.resize(image, (thumb_width, int(h * scale))))
    if not thumbs:
        return

    cols = max(1, cols)
    thumb_h = max(thumb.shape[0] for thumb in thumbs)
    rows = math.ceil(len(thumbs) / cols)
    sheet = np.zeros((rows * thumb_h, cols * thumb_width, 3), dtype=np.uint8)
    for index, thumb in enumerate(thumbs):
        row = index // cols
        col = index % cols
        y = row * thumb_h
        x = col * thumb_width
        sheet[y : y + thumb.shape[0], x : x + thumb.shape[1]] = thumb
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), sheet)


def main() -> None:
    args = parse_args()
    if not args.detections.exists():
        raise SystemExit(f"Detections CSV not found: {args.detections}")

    rows = load_rows(args.detections, args.class_name, args.min_conf)
    rows.sort(key=lambda row: float(row["confidence"]), reverse=True)
    if args.top_k > 0:
        rows = rows[: args.top_k]

    grouped = group_by_image(rows)
    review_dir = args.output_root / "images"
    review_dir.mkdir(parents=True, exist_ok=True)
    review_paths: list[Path] = []
    missing = 0

    for index, image_rows in enumerate(grouped.values(), start=1):
        image = draw_rows(Path(image_rows[0]["image_path"]), image_rows)
        if image is None:
            missing += 1
            continue
        review_path = review_dir / safe_name(index, image_rows)
        cv2.imwrite(str(review_path), image)
        review_paths.append(review_path)

    write_contact_sheet(
        review_paths,
        args.output_root / "contact_sheet.jpg",
        cols=args.contact_sheet_cols,
        thumb_width=args.contact_sheet_thumb_width,
    )

    print(f"detections: {args.detections}")
    print(f"rows selected: {len(rows)}")
    print(f"review images: {len(review_paths)}")
    print(f"missing images: {missing}")
    print(f"output: {review_dir}")
    print(f"contact sheet: {args.output_root / 'contact_sheet.jpg'}")


if __name__ == "__main__":
    main()
