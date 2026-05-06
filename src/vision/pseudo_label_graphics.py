"""Create YOLO pseudo-labels from detector CSV outputs."""

from __future__ import annotations

import argparse
import csv
import shutil
from collections import defaultdict
from pathlib import Path

import cv2


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert high-confidence detections into YOLO pseudo-labels.")
    parser.add_argument("--detections", required=True, type=Path, help="Detection CSV path.")
    parser.add_argument(
        "--output-root",
        default=Path("datasets/yolo_broadcast_graphics_pseudo"),
        type=Path,
        help="Output YOLO dataset root for pseudo-label candidates.",
    )
    parser.add_argument("--class-name", default="scoreboard", help="Class to keep from detection CSV.")
    parser.add_argument("--class-id", type=int, default=0, help="YOLO class id to write.")
    parser.add_argument("--min-conf", type=float, default=0.70, help="Minimum confidence to accept.")
    parser.add_argument("--max-images", type=int, default=0, help="Optional cap for accepted images.")
    parser.add_argument("--copy-images", action="store_true", help="Copy accepted source images into output dataset.")
    parser.add_argument(
        "--review-dir",
        default=Path("outputs/pseudo_labels/review"),
        type=Path,
        help="Directory for review images with accepted boxes drawn.",
    )
    parser.add_argument("--no-review-images", action="store_true")
    return parser.parse_args()


def yolo_line(class_id: int, box: tuple[float, float, float, float], width: int, height: int) -> str:
    x1, y1, x2, y2 = box
    x_center = ((x1 + x2) / 2) / width
    y_center = ((y1 + y2) / 2) / height
    box_width = (x2 - x1) / width
    box_height = (y2 - y1) / height
    return f"{class_id} {x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"


def target_name(image_path: Path) -> str:
    half = next((part for part in image_path.parts if part.startswith("half_")), "half_unknown")
    return f"{half}__{image_path.stem}"


def draw_review(image, boxes: list[tuple[float, float, float, float, float]], class_name: str):
    output = image.copy()
    for x1, y1, x2, y2, conf in boxes:
        pt1 = (int(round(x1)), int(round(y1)))
        pt2 = (int(round(x2)), int(round(y2)))
        cv2.rectangle(output, pt1, pt2, (0, 255, 255), 2)
        cv2.putText(
            output,
            f"{class_name} {conf:.2f}",
            (pt1[0], max(20, pt1[1] - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            (0, 255, 255),
            2,
            cv2.LINE_AA,
        )
    return output


def main() -> None:
    args = parse_args()
    if not args.detections.exists():
        raise SystemExit(f"Detection CSV not found: {args.detections}")

    by_image: dict[Path, list[tuple[float, float, float, float, float]]] = defaultdict(list)
    with args.detections.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["class_name"] != args.class_name:
                continue
            confidence = float(row["confidence"])
            if confidence < args.min_conf:
                continue
            image_path = Path(row["image_path"])
            by_image[image_path].append(
                (
                    float(row["x1"]),
                    float(row["y1"]),
                    float(row["x2"]),
                    float(row["y2"]),
                    confidence,
                )
            )

    accepted = list(sorted(by_image.items(), key=lambda item: item[0].as_posix()))
    if args.max_images > 0:
        accepted = accepted[: args.max_images]

    image_out = args.output_root / "images" / "train"
    label_out = args.output_root / "labels" / "train"
    image_out.mkdir(parents=True, exist_ok=True)
    label_out.mkdir(parents=True, exist_ok=True)
    if not args.no_review_images:
        args.review_dir.mkdir(parents=True, exist_ok=True)

    written = 0
    missing_images = 0
    for image_path, boxes in accepted:
        image = cv2.imread(str(image_path))
        if image is None:
            missing_images += 1
            continue
        height, width = image.shape[:2]
        name = target_name(image_path)
        label_path = label_out / f"{name}.txt"
        lines = [
            yolo_line(args.class_id, (x1, y1, x2, y2), width, height)
            for x1, y1, x2, y2, _ in boxes
        ]
        label_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

        if args.copy_images:
            shutil.copy2(image_path, image_out / f"{name}{image_path.suffix.lower()}")
        if not args.no_review_images:
            review = draw_review(image, boxes, args.class_name)
            cv2.imwrite(str(args.review_dir / f"{name}.jpg"), review)
        written += 1

    data_yaml = args.output_root / "data.yaml"
    if not data_yaml.exists():
        data_yaml.write_text(
            "\n".join(
                [
                    f"path: /app/{args.output_root.as_posix()}",
                    "train: images/train",
                    "val: images/train",
                    "names:",
                    "  0: scoreboard",
                    "  1: overlay",
                    "  2: replay_logo",
                    "",
                ]
            ),
            encoding="utf-8",
        )

    print(f"detections: {args.detections}")
    print(f"accepted images: {written}")
    print(f"missing images: {missing_images}")
    print(f"labels: {label_out}")
    if args.copy_images:
        print(f"images: {image_out}")
    if not args.no_review_images:
        print(f"review images: {args.review_dir}")


if __name__ == "__main__":
    main()
