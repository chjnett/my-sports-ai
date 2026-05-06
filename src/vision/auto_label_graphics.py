"""Create heuristic YOLO labels for broadcast graphics.

This is a bootstrap tool, not a final annotator. It creates first-pass labels
for stable broadcast graphics so a human can review and correct them before
training.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


CLASSES = {
    "scoreboard": 0,
    "overlay": 1,
    "replay_logo": 2,
}


@dataclass(frozen=True)
class Box:
    class_id: int
    x1: int
    y1: int
    x2: int
    y2: int
    confidence: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate first-pass YOLO labels for scoreboard/replay broadcast graphics."
    )
    parser.add_argument(
        "--dataset-root",
        type=Path,
        default=Path("datasets/yolo_broadcast_graphics"),
        help="YOLO dataset root containing images/{train,val} and labels/{train,val}.",
    )
    parser.add_argument(
        "--splits",
        nargs="+",
        default=["train", "val"],
        choices=["train", "val"],
        help="Dataset splits to auto-label.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite existing label txt files.",
    )
    parser.add_argument(
        "--review-dir",
        type=Path,
        default=Path("outputs/auto_labels/yolo_broadcast_graphics"),
        help="Directory for annotated review images.",
    )
    parser.add_argument(
        "--no-review-images",
        action="store_true",
        help="Do not write annotated review images.",
    )
    parser.add_argument(
        "--include-replay-logo-candidates",
        action="store_true",
        help=(
            "Also write rough replay_logo candidates. This is intentionally off "
            "by default because general play can look like a centered logo."
        ),
    )
    return parser.parse_args()


def clamp_box(box: Box, width: int, height: int) -> Box:
    return Box(
        class_id=box.class_id,
        x1=max(0, min(width - 1, box.x1)),
        y1=max(0, min(height - 1, box.y1)),
        x2=max(0, min(width - 1, box.x2)),
        y2=max(0, min(height - 1, box.y2)),
        confidence=box.confidence,
    )


def to_yolo_line(box: Box, width: int, height: int) -> str:
    x_center = ((box.x1 + box.x2) / 2) / width
    y_center = ((box.y1 + box.y2) / 2) / height
    box_width = (box.x2 - box.x1) / width
    box_height = (box.y2 - box.y1) / height
    return (
        f"{box.class_id} "
        f"{x_center:.6f} {y_center:.6f} {box_width:.6f} {box_height:.6f}"
    )


def timestamp_ms_from_path(image_path: Path) -> int | None:
    try:
        return int(image_path.stem.split("__")[-1])
    except (IndexError, ValueError):
        return None


def detect_scoreboard(image: np.ndarray, image_path: Path) -> Box | None:
    """Detect the EPL-style top-left scoreboard used in the target match."""
    height, width = image.shape[:2]

    timestamp_ms = timestamp_ms_from_path(image_path)
    if timestamp_ms is not None and timestamp_ms < 5000:
        return None

    # The target broadcast places the scoreboard in the upper-left. This ROI is
    # intentionally wide enough to include the Premier League icon, teams, score,
    # and timer, while avoiding the top-right channel bug.
    roi_x1 = int(width * 0.045)
    roi_y1 = int(height * 0.035)
    roi_x2 = int(width * 0.330)
    roi_y2 = int(height * 0.190)
    roi = image[roi_y1:roi_y2, roi_x1:roi_x2]

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    bright = gray > 175
    blue = (hsv[:, :, 0] > 85) & (hsv[:, :, 0] < 135) & (hsv[:, :, 1] > 35)
    dark_text = gray < 65
    graphic_mask = (bright | blue | dark_text).astype(np.uint8) * 255

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 5))
    graphic_mask = cv2.morphologyEx(graphic_mask, cv2.MORPH_CLOSE, kernel)
    contours, _ = cv2.findContours(graphic_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    candidates: list[tuple[int, int, int, int, int]] = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        if area < 900 or w < 45 or h < 18:
            continue
        candidates.append((x, y, w, h, area))

    if not candidates:
        return None

    x_min = min(x for x, _, _, _, _ in candidates)
    y_min = min(y for _, y, _, _, _ in candidates)
    x_max = max(x + w for x, y, w, h, _ in candidates)
    y_max = max(y + h for x, y, w, h, _ in candidates)
    combined_area = (x_max - x_min) * (y_max - y_min)

    white_ratio = float(np.mean(bright))
    blue_ratio = float(np.mean(blue))
    if combined_area < 3200 or (white_ratio < 0.055 and blue_ratio < 0.012):
        return None

    # For this EPL feed the scoreboard geometry is very stable. After detecting
    # that the graphic is present, use a tight fixed box instead of the loose
    # connected-component bounds, which often absorb crowd banners.
    fixed = Box(
        class_id=CLASSES["scoreboard"],
        x1=int(width * 0.083),
        y1=int(height * 0.052),
        x2=int(width * 0.285),
        y2=int(height * 0.150),
        confidence=min(0.99, white_ratio * 3.0 + blue_ratio * 4.0),
    )
    return clamp_box(fixed, width, height)


def detect_replay_logo(image: np.ndarray) -> Box | None:
    """Detect a centered replay transition logo candidate."""
    height, width = image.shape[:2]
    roi_x1 = int(width * 0.275)
    roi_y1 = int(height * 0.200)
    roi_x2 = int(width * 0.725)
    roi_y2 = int(height * 0.800)
    roi = image[roi_y1:roi_y2, roi_x1:roi_x2]

    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 70, 170)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (13, 13))
    edges = cv2.dilate(edges, kernel, iterations=1)

    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    best: tuple[int, int, int, int, int] | None = None
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        area = w * h
        aspect = w / max(h, 1)
        center_x = (x + w / 2) / max(roi.shape[1], 1)
        center_y = (y + h / 2) / max(roi.shape[0], 1)
        centered = 0.28 < center_x < 0.72 and 0.25 < center_y < 0.75
        if not centered:
            continue
        if area < (width * height * 0.012):
            continue
        if not 0.55 <= aspect <= 1.85:
            continue
        if best is None or area > best[4]:
            best = (x, y, w, h, area)

    if best is None:
        return None

    x, y, w, h, area = best
    # Avoid labeling the center circle or general play as replay_logo. A replay
    # logo candidate should be a compact, centered graphic, not a huge pitch area.
    if area > width * height * 0.18:
        return None

    pad_x = int(width * 0.015)
    pad_y = int(height * 0.020)
    return clamp_box(
        Box(
            class_id=CLASSES["replay_logo"],
            x1=roi_x1 + x - pad_x,
            y1=roi_y1 + y - pad_y,
            x2=roi_x1 + x + w + pad_x,
            y2=roi_y1 + y + h + pad_y,
            confidence=min(0.99, area / (width * height * 0.05)),
        ),
        width,
        height,
    )


def auto_label_image(image_path: Path, include_replay_logo_candidates: bool) -> tuple[list[Box], np.ndarray]:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    boxes: list[Box] = []
    scoreboard = detect_scoreboard(image, image_path)
    if scoreboard is not None:
        boxes.append(scoreboard)

    if include_replay_logo_candidates:
        replay_logo = detect_replay_logo(image)
        if replay_logo is not None:
            boxes.append(replay_logo)

    return boxes, image


def draw_review(image: np.ndarray, boxes: list[Box]) -> np.ndarray:
    output = image.copy()
    colors = {
        CLASSES["scoreboard"]: (0, 255, 255),
        CLASSES["overlay"]: (255, 0, 255),
        CLASSES["replay_logo"]: (0, 255, 0),
    }
    names = {value: key for key, value in CLASSES.items()}
    for box in boxes:
        color = colors.get(box.class_id, (255, 255, 255))
        cv2.rectangle(output, (box.x1, box.y1), (box.x2, box.y2), color, 2)
        label = f"{names.get(box.class_id, box.class_id)} {box.confidence:.2f}"
        cv2.putText(
            output,
            label,
            (box.x1, max(20, box.y1 - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            color,
            2,
            cv2.LINE_AA,
        )
    return output


def process_split(
    dataset_root: Path,
    split: str,
    review_dir: Path,
    overwrite: bool,
    write_review: bool,
    include_replay_logo_candidates: bool,
) -> dict[str, int]:
    image_dir = dataset_root / "images" / split
    label_dir = dataset_root / "labels" / split
    split_review_dir = review_dir / split
    label_dir.mkdir(parents=True, exist_ok=True)
    if write_review:
        split_review_dir.mkdir(parents=True, exist_ok=True)

    stats = {
        "images": 0,
        "written": 0,
        "skipped_existing": 0,
        "scoreboard": 0,
        "replay_logo": 0,
        "empty": 0,
    }
    for image_path in sorted(image_dir.glob("*.jpg")):
        stats["images"] += 1
        label_path = label_dir / f"{image_path.stem}.txt"
        if label_path.exists() and not overwrite:
            stats["skipped_existing"] += 1
            continue

        boxes, image = auto_label_image(image_path, include_replay_logo_candidates)
        height, width = image.shape[:2]
        lines = [to_yolo_line(box, width, height) for box in boxes]
        label_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")

        if write_review:
            review = draw_review(image, boxes)
            cv2.imwrite(str(split_review_dir / image_path.name), review)

        stats["written"] += 1
        if not boxes:
            stats["empty"] += 1
        for box in boxes:
            if box.class_id == CLASSES["scoreboard"]:
                stats["scoreboard"] += 1
            elif box.class_id == CLASSES["replay_logo"]:
                stats["replay_logo"] += 1

    return stats


def main() -> None:
    args = parse_args()
    total = {
        "images": 0,
        "written": 0,
        "skipped_existing": 0,
        "scoreboard": 0,
        "replay_logo": 0,
        "empty": 0,
    }
    for split in args.splits:
        stats = process_split(
            dataset_root=args.dataset_root,
            split=split,
            review_dir=args.review_dir,
            overwrite=args.overwrite,
            write_review=not args.no_review_images,
            include_replay_logo_candidates=args.include_replay_logo_candidates,
        )
        for key, value in stats.items():
            total[key] += value
        print(f"{split}: {stats}")

    print(f"total: {total}")
    if not args.no_review_images:
        print(f"review images: {args.review_dir}")


if __name__ == "__main__":
    main()
