"""Run PaddleOCR on scoreboard crop images."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Any

from tqdm import tqdm

from src.ocr.scoreboard_text import parse_clock, parse_score


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run OCR on scoreboard detection crops.")
    parser.add_argument("--crops", required=True, type=Path, help="Crop summary CSV from crop_detections.py.")
    parser.add_argument("--output", required=True, type=Path, help="Output OCR CSV.")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--lang", default="en")
    parser.add_argument("--device", default="gpu", choices=["gpu", "cpu"])
    parser.add_argument("--use-angle-cls", action="store_true")
    return parser.parse_args()


def make_ocr(lang: str, device: str, use_angle_cls: bool) -> Any:
    from paddleocr import PaddleOCR

    use_gpu = device == "gpu"
    try:
        return PaddleOCR(lang=lang, use_gpu=use_gpu, use_angle_cls=use_angle_cls)
    except ValueError:
        # PaddleOCR 3.x moved toward device strings.
        return PaddleOCR(lang=lang, device=device, use_textline_orientation=use_angle_cls)


def flatten_ocr_result(result: Any) -> tuple[str, float]:
    texts: list[str] = []
    confidences: list[float] = []

    def visit(node: Any) -> None:
        if node is None:
            return
        if isinstance(node, dict):
            for key in ["rec_texts", "rec_scores"]:
                if key in node:
                    value = node[key]
                    if key == "rec_texts":
                        texts.extend(str(item) for item in value)
                    else:
                        confidences.extend(float(item) for item in value)
            return
        if isinstance(node, (list, tuple)):
            if len(node) == 2 and isinstance(node[1], (list, tuple)) and len(node[1]) >= 2:
                text = node[1][0]
                score = node[1][1]
                if isinstance(text, str):
                    texts.append(text)
                    try:
                        confidences.append(float(score))
                    except (TypeError, ValueError):
                        pass
                    return
            for item in node:
                visit(item)

    visit(result)
    raw_text = " ".join(texts).strip()
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    return raw_text, avg_conf


def run_ocr(ocr: Any, image_path: Path) -> Any:
    if hasattr(ocr, "predict"):
        return ocr.predict(str(image_path))
    if hasattr(ocr, "ocr"):
        return ocr.ocr(str(image_path), cls=False)
    raise RuntimeError("Unsupported PaddleOCR object: no ocr() or predict() method")


def main() -> None:
    args = parse_args()
    if not args.crops.exists():
        raise SystemExit(f"Crop summary CSV not found: {args.crops}")

    with args.crops.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if args.limit > 0:
        rows = rows[: args.limit]

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
        for row in tqdm(rows, desc="OCR scoreboard", unit="crop", dynamic_ncols=True):
            crop_image = Path(row["crop_image"])
            if not crop_image.exists():
                continue
            try:
                result = run_ocr(ocr, crop_image)
                raw_text, ocr_confidence = flatten_ocr_result(result)
            except Exception as exc:  # noqa: BLE001 - keep batch OCR moving.
                raw_text = f"OCR_ERROR: {exc}"
                ocr_confidence = 0.0
            home_score, away_score = parse_score(raw_text)
            writer.writerow(
                {
                    "class_name": row["class_name"],
                    "half": row["half"],
                    "timestamp_sec": row["timestamp_sec"],
                    "det_confidence": row["confidence"],
                    "ocr_confidence": round(ocr_confidence, 6),
                    "raw_text": raw_text,
                    "parsed_clock": parse_clock(raw_text),
                    "parsed_home_score": home_score,
                    "parsed_away_score": away_score,
                    "crop_image": row["crop_image"],
                    "source_image": row["source_image"],
                }
            )
            written += 1

    print(f"crops: {args.crops}")
    print(f"rows selected: {len(rows)}")
    print(f"ocr rows written: {written}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
