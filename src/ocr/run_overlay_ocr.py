"""Run PaddleOCR on the lower-third overlay region of sampled frames."""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

import cv2
from tqdm import tqdm

from src.ocr.run_scoreboard_ocr import flatten_ocr_result, make_ocr

TIMESTAMP_RE = re.compile(r"(?P<timestamp_ms>\d{10})\.jpg$", re.IGNORECASE)


def infer_half(image_path: Path) -> int | None:
    for part in image_path.parts:
        if part.startswith("half_"):
            try:
                return int(part.split("_", 1)[1])
            except ValueError:
                return None
    return None


def infer_timestamp_sec(image_path: Path) -> float | None:
    match = TIMESTAMP_RE.search(image_path.name)
    if not match:
        return None
    return int(match.group("timestamp_ms")) / 1000.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OCR on the lower-third overlay of all frames.")
    parser.add_argument("--frames-root", required=True, type=Path, help="Root directory of frames to process.")
    parser.add_argument("--output", required=True, type=Path, help="Output OCR CSV.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--lang", default="en")
    parser.add_argument("--device", default="gpu", choices=["gpu", "cpu"])
    parser.add_argument("--use-angle-cls", action="store_true")
    parser.add_argument("--step", type=int, default=1, help="Process every Nth frame.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if not args.frames_root.exists():
        raise SystemExit(f"Frames root not found: {args.frames_root}")

    images = sorted(args.frames_root.rglob("*.jpg"))
    if args.step > 1:
        images = images[::args.step]
    if args.limit > 0:
        images = images[: args.limit]

    ocr = make_ocr(args.lang, args.device, args.use_angle_cls)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "class_name",
        "half",
        "timestamp_sec",
        "det_confidence",
        "ocr_confidence",
        "raw_text",
        "parsed_clock",
        "parsed_home_score",
        "parsed_away_score",
        "crop_image",
        "source_image",
    ]

    written = 0
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for image_path in tqdm(images, desc="OCR overlay", unit="frame", dynamic_ncols=True):
            image = cv2.imread(str(image_path))
            if image is None:
                continue

            H, W = image.shape[:2]
            y1, y2 = int(H * 0.75), H
            x1, x2 = int(W * 0.1), int(W * 0.9)
            crop = image[y1:y2, x1:x2]

            try:
                if hasattr(ocr, "predict"):
                    result = ocr.predict(crop)
                elif hasattr(ocr, "ocr"):
                    result = ocr.ocr(crop, cls=False)
                else:
                    raise RuntimeError("Unsupported PaddleOCR object")

                raw_text, ocr_confidence = flatten_ocr_result(result)
            except Exception as exc:  # noqa: BLE001
                raw_text = f"OCR_ERROR: {exc}"
                ocr_confidence = 0.0

            if not raw_text:
                continue

            writer.writerow(
                {
                    "class_name": "overlay",
                    "half": infer_half(image_path),
                    "timestamp_sec": infer_timestamp_sec(image_path),
                    "det_confidence": 1.0,
                    "ocr_confidence": round(ocr_confidence, 6),
                    "raw_text": raw_text,
                    "parsed_clock": "",
                    "parsed_home_score": "",
                    "parsed_away_score": "",
                    "crop_image": "",
                    "source_image": image_path.as_posix(),
                }
            )
            written += 1

    print(f"frames scanned: {len(images)}")
    print(f"overlay text found: {written}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
