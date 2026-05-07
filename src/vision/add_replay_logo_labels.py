"""Add replay_logo candidates to a YOLO dataset."""

from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

import cv2
import yaml


CLASSES = {
    0: "scoreboard",
    1: "overlay",
    2: "replay_logo",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert reviewed replay logo candidates into YOLO labels.")
    parser.add_argument("--candidates", required=True, type=Path, help="Replay logo candidates CSV.")
    parser.add_argument(
        "--dataset-root",
        default=Path("datasets/yolo_broadcast_graphics_replay_logo"),
        type=Path,
        help="Output YOLO dataset root.",
    )
    parser.add_argument("--split", default="train", choices=["train", "val"], help="Target split.")
    parser.add_argument("--class-id", type=int, default=2)
    parser.add_argument(
        "--ranks",
        nargs="*",
        type=int,
        default=[],
        help="Optional accepted candidate ranks. If omitted, all rows are accepted.",
    )
    parser.add_argument("--copy-images", action="store_true", default=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def write_data_yaml(dataset_root: Path) -> None:
    payload = {
        "path": f"/app/{dataset_root.as_posix()}",
        "train": "images/train",
        "val": "images/val",
        "names": CLASSES,
    }
    with (dataset_root / "data.yaml").open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)


def yolo_line(class_id: int, box: tuple[float, float, float, float], width: int, height: int) -> str:
    x1, y1, x2, y2 = box
    x_center = ((x1 + x2) / 2) / width
    y_center = ((y1 + y2) / 2) / height
    box_width = (x2 - x1) / width
    box_height = (y2 - y1) / height
    return f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"


def target_stem(row: dict[str, str]) -> str:
    timestamp = row["timestamp_sec"].replace(".", "p")
    return f"replay_logo__rank_{int(row['rank']):04d}__{row['half']}__{timestamp}s"


def main() -> None:
    args = parse_args()
    if not args.candidates.exists():
        raise SystemExit(f"Candidates CSV not found: {args.candidates}")

    image_dir = args.dataset_root / "images" / args.split
    label_dir = args.dataset_root / "labels" / args.split
    image_dir.mkdir(parents=True, exist_ok=True)
    label_dir.mkdir(parents=True, exist_ok=True)
    for split in ["train", "val"]:
        (args.dataset_root / "images" / split).mkdir(parents=True, exist_ok=True)
        (args.dataset_root / "labels" / split).mkdir(parents=True, exist_ok=True)
        (args.dataset_root / "images" / split / ".gitkeep").touch(exist_ok=True)
        (args.dataset_root / "labels" / split / ".gitkeep").touch(exist_ok=True)

    accepted_ranks = set(args.ranks)
    written = 0
    skipped = 0
    with args.candidates.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            rank = int(row["rank"])
            if accepted_ranks and rank not in accepted_ranks:
                skipped += 1
                continue

            image_path = Path(row["image_path"])
            image = cv2.imread(str(image_path))
            if image is None:
                skipped += 1
                continue
            height, width = image.shape[:2]
            stem = target_stem(row)
            output_image = image_dir / f"{stem}{image_path.suffix.lower()}"
            output_label = label_dir / f"{stem}.txt"
            if output_label.exists() and not args.overwrite:
                skipped += 1
                continue

            line = yolo_line(
                args.class_id,
                (
                    float(row["x1"]),
                    float(row["y1"]),
                    float(row["x2"]),
                    float(row["y2"]),
                ),
                width,
                height,
            )
            output_label.write_text(line + "\n", encoding="utf-8")
            if args.copy_images:
                shutil.copy2(image_path, output_image)
            written += 1

    write_data_yaml(args.dataset_root)
    print(f"candidates: {args.candidates}")
    print(f"dataset: {args.dataset_root}")
    print(f"split: {args.split}")
    print(f"written replay_logo labels: {written}")
    print(f"skipped: {skipped}")
    print(f"images: {image_dir}")
    print(f"labels: {label_dir}")


if __name__ == "__main__":
    main()
