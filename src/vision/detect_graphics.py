from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

from tqdm import tqdm
from ultralytics import YOLO


TIMESTAMP_RE = re.compile(r"(?P<timestamp_ms>\d{10})\.jpg$", re.IGNORECASE)


def iter_images(frames_root: Path) -> list[Path]:
    return sorted(frames_root.rglob("*.jpg"))


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


def infer_match_id(image_path: Path, frames_root: Path) -> str:
    try:
        relative = image_path.relative_to(frames_root)
    except ValueError:
        return frames_root.name
    parts = list(relative.parts)
    if parts and parts[-1].endswith(".jpg"):
        parts = parts[:-1]
    if parts and parts[-1].startswith("half_"):
        parts = parts[:-1]
    return "/".join(parts) if parts else frames_root.name


def main() -> None:
    parser = argparse.ArgumentParser(description="Run YOLO broadcast graphics detection on sampled frames.")
    parser.add_argument("--model", required=True, help="Path to trained YOLO model.")
    parser.add_argument("--frames-root", required=True, help="Frame root to scan recursively.")
    parser.add_argument("--output", default="outputs/detections/detections.csv", help="CSV output path.")
    parser.add_argument("--conf", type=float, default=0.25)
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--device", default=0, help="CUDA device id or 'cpu'.")
    parser.add_argument("--limit", type=int, default=0, help="Optional max images for smoke tests.")
    args = parser.parse_args()

    frames_root = Path(args.frames_root)
    images = iter_images(frames_root)
    if args.limit > 0:
        images = images[: args.limit]
    if not images:
        raise SystemExit(f"No images found under: {frames_root}")

    model = YOLO(args.model)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "match_id",
        "half",
        "timestamp_sec",
        "class_id",
        "class_name",
        "confidence",
        "x1",
        "y1",
        "x2",
        "y2",
        "image_path",
    ]

    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for image in tqdm(images, desc="Detecting", unit="image", dynamic_ncols=True):
            results = model.predict(
                source=str(image),
                conf=args.conf,
                imgsz=args.imgsz,
                device=args.device,
                verbose=False,
            )
            result = results[0]
            names = result.names
            half = infer_half(image)
            timestamp_sec = infer_timestamp_sec(image)
            match_id = infer_match_id(image, frames_root)

            for box in result.boxes:
                class_id = int(box.cls.item())
                confidence = float(box.conf.item())
                x1, y1, x2, y2 = [float(value) for value in box.xyxy[0].tolist()]
                writer.writerow(
                    {
                        "match_id": match_id,
                        "half": half,
                        "timestamp_sec": timestamp_sec,
                        "class_id": class_id,
                        "class_name": names.get(class_id, str(class_id)),
                        "confidence": confidence,
                        "x1": round(x1, 3),
                        "y1": round(y1, 3),
                        "x2": round(x2, 3),
                        "y2": round(y2, 3),
                        "image_path": image.as_posix(),
                    }
                )

    print(f"wrote detections: {output}")
    print(f"processed images: {len(images)}")


if __name__ == "__main__":
    main()
