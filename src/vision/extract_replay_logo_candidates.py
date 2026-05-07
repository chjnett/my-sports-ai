"""Extract likely replay transition logo frames.

The Premier League replay transition in the target match is a centered graphic
that appears briefly before/after replay segments. This tool ranks sampled
frames by centered graphic saliency and writes review images so humans only need
to inspect the strongest candidates.
"""

from __future__ import annotations

import argparse
import csv
import math
import shutil
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np


@dataclass(frozen=True)
class Candidate:
    score: float
    image_path: Path
    half: str
    timestamp_sec: float | None
    edge_density: float
    non_green_ratio: float
    largest_component_ratio: float
    box_area_ratio: float
    box_aspect_ratio: float
    logo_color_ratio: float
    magenta_ratio: float
    center_distance: float
    x1: int
    y1: int
    x2: int
    y2: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank frames likely to contain centered replay transition logos.")
    parser.add_argument("--frames-root", required=True, type=Path, help="Root containing half_* frame folders.")
    parser.add_argument(
        "--output-root",
        default=Path("outputs/replay_logo_candidates"),
        type=Path,
        help="Output directory for candidate CSV and review images.",
    )
    parser.add_argument("--top-k", type=int, default=100, help="Number of strongest candidates to copy.")
    parser.add_argument("--stride", type=int, default=1, help="Analyze every Nth frame.")
    parser.add_argument("--min-score", type=float, default=0.25, help="Minimum score to include.")
    parser.add_argument(
        "--min-box-area-ratio",
        type=float,
        default=0.10,
        help="Minimum candidate box area as a fraction of the full frame.",
    )
    parser.add_argument(
        "--max-box-area-ratio",
        type=float,
        default=0.40,
        help="Maximum candidate box area as a fraction of the full frame.",
    )
    parser.add_argument(
        "--max-center-distance",
        type=float,
        default=0.45,
        help="Maximum normalized distance from the center of the central ROI.",
    )
    parser.add_argument(
        "--min-box-aspect-ratio",
        type=float,
        default=0.70,
        help="Minimum candidate bbox width/height ratio.",
    )
    parser.add_argument(
        "--max-box-aspect-ratio",
        type=float,
        default=1.90,
        help="Maximum candidate bbox width/height ratio.",
    )
    parser.add_argument(
        "--min-logo-color-ratio",
        type=float,
        default=0.035,
        help="Minimum white/navy/magenta logo-color pixel ratio inside the candidate box.",
    )
    parser.add_argument(
        "--min-magenta-ratio",
        type=float,
        default=0.0025,
        help="Minimum magenta/red ball-like pixel ratio inside the candidate box.",
    )
    parser.add_argument("--copy-originals", action="store_true", help="Copy raw candidate frames too.")
    parser.add_argument("--contact-sheet-cols", type=int, default=5)
    parser.add_argument("--contact-sheet-thumb-width", type=int, default=320)
    return parser.parse_args()


def collect_frames(frames_root: Path, stride: int) -> list[Path]:
    frames = sorted(frames_root.rglob("*.jpg"))
    return frames[:: max(1, stride)]


def infer_half(path: Path) -> str:
    for part in path.parts:
        if part.startswith("half_"):
            return part
    return "half_unknown"


def infer_timestamp_sec(path: Path) -> float | None:
    try:
        return int(path.stem) / 1000.0
    except ValueError:
        return None


def central_roi(width: int, height: int) -> tuple[int, int, int, int]:
    return (
        int(width * 0.26),
        int(height * 0.18),
        int(width * 0.74),
        int(height * 0.82),
    )


def score_frame(image_path: Path) -> Candidate | None:
    image = cv2.imread(str(image_path))
    if image is None:
        return None

    height, width = image.shape[:2]
    x1, y1, x2, y2 = central_roi(width, height)
    roi = image[y1:y2, x1:x2]
    roi_h, roi_w = roi.shape[:2]
    if roi_h == 0 or roi_w == 0:
        return None

    hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
    gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    # Pitch and live-play backgrounds are mostly green. The transition logo
    # tends to create a dense, centered, non-green graphic footprint.
    hue = hsv[:, :, 0]
    sat = hsv[:, :, 1]
    val = hsv[:, :, 2]
    green = (hue >= 32) & (hue <= 92) & (sat >= 35) & (val >= 35)
    bright = val >= 175
    colorful = sat >= 80
    dark_graphic = val <= 55
    non_green_graphic = (~green) & (bright | colorful | dark_graphic)
    white_logo = (sat <= 60) & (val >= 175)
    navy_logo = (hue >= 92) & (hue <= 135) & (sat >= 45) & (val <= 210)
    magenta_logo = (((hue <= 12) | (hue >= 155)) & (sat >= 55) & (val >= 95))
    logo_color_graphic = white_logo | navy_logo | magenta_logo

    edges = cv2.Canny(gray, 80, 180)
    edge_density = float(np.mean(edges > 0))
    non_green_ratio = float(np.mean(non_green_graphic))

    # Use Premier-League-logo-like colors for the component box. This is much
    # stricter than generic non-green saliency and reduces player/bench closeups.
    mask = (logo_color_graphic.astype(np.uint8) * 255)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.dilate(mask, kernel, iterations=1)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    roi_area = roi_w * roi_h
    best_component: tuple[int, int, int, int, float, float] | None = None
    for contour in contours:
        cx, cy, cw, ch = cv2.boundingRect(contour)
        area = float(cw * ch)
        if area < roi_area * 0.005:
            continue
        center_x = cx + cw / 2
        center_y = cy + ch / 2
        normalized_distance = math.sqrt(
            ((center_x - roi_w / 2) / max(roi_w / 2, 1)) ** 2
            + ((center_y - roi_h / 2) / max(roi_h / 2, 1)) ** 2
        )
        if best_component is None or area > best_component[4]:
            best_component = (cx, cy, cw, ch, area, normalized_distance)

    if best_component is None:
        component_ratio = 0.0
        center_distance = 1.5
        bx1 = x1 + int(roi_w * 0.35)
        by1 = y1 + int(roi_h * 0.25)
        bx2 = x1 + int(roi_w * 0.65)
        by2 = y1 + int(roi_h * 0.75)
    else:
        cx, cy, cw, ch, area, center_distance = best_component
        component_ratio = area / roi_area
        pad_x = int(width * 0.015)
        pad_y = int(height * 0.020)
        bx1 = max(0, x1 + cx - pad_x)
        by1 = max(0, y1 + cy - pad_y)
        bx2 = min(width - 1, x1 + cx + cw + pad_x)
        by2 = min(height - 1, y1 + cy + ch + pad_y)

    box_w = max(1, bx2 - bx1)
    box_h = max(1, by2 - by1)
    box_area_ratio = (box_w * box_h) / (width * height)
    box_aspect_ratio = box_w / box_h
    box_roi = image[by1:by2, bx1:bx2]
    if box_roi.size == 0:
        logo_color_ratio = 0.0
        magenta_ratio = 0.0
    else:
        box_hsv = cv2.cvtColor(box_roi, cv2.COLOR_BGR2HSV)
        box_hue = box_hsv[:, :, 0]
        box_sat = box_hsv[:, :, 1]
        box_val = box_hsv[:, :, 2]
        box_white = (box_sat <= 60) & (box_val >= 175)
        box_navy = (box_hue >= 92) & (box_hue <= 135) & (box_sat >= 45) & (box_val <= 210)
        box_magenta = (((box_hue <= 12) | (box_hue >= 155)) & (box_sat >= 55) & (box_val >= 95))
        logo_color_ratio = float(np.mean(box_white | box_navy | box_magenta))
        magenta_ratio = float(np.mean(box_magenta))

    center_bonus = max(0.0, 1.0 - center_distance)
    # Balanced to rank transition graphics high while still allowing candidates
    # with moderate edge density but strong centered non-green components.
    score = (
        component_ratio * 4.0
        + non_green_ratio * 1.25
        + edge_density * 0.75
        + center_bonus * 0.45
    )

    return Candidate(
        score=score,
        image_path=image_path,
        half=infer_half(image_path),
        timestamp_sec=infer_timestamp_sec(image_path),
        edge_density=edge_density,
        non_green_ratio=non_green_ratio,
        largest_component_ratio=component_ratio,
        box_area_ratio=box_area_ratio,
        box_aspect_ratio=box_aspect_ratio,
        logo_color_ratio=logo_color_ratio,
        magenta_ratio=magenta_ratio,
        center_distance=center_distance,
        x1=bx1,
        y1=by1,
        x2=bx2,
        y2=by2,
    )


def draw_review(candidate: Candidate) -> np.ndarray | None:
    image = cv2.imread(str(candidate.image_path))
    if image is None:
        return None
    height, width = image.shape[:2]
    rx1, ry1, rx2, ry2 = central_roi(width, height)
    cv2.rectangle(image, (rx1, ry1), (rx2, ry2), (255, 0, 255), 2)
    cv2.rectangle(image, (candidate.x1, candidate.y1), (candidate.x2, candidate.y2), (0, 255, 0), 2)
    label = (
        f"score={candidate.score:.3f} "
        f"area={candidate.box_area_ratio:.3f} "
        f"mag={candidate.magenta_ratio:.3f} "
        f"{candidate.half} t={candidate.timestamp_sec}"
    )
    cv2.putText(
        image,
        label,
        (20, 32),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (0, 255, 0),
        2,
        cv2.LINE_AA,
    )
    return image


def output_name(rank: int, candidate: Candidate) -> str:
    timestamp = "unknown" if candidate.timestamp_sec is None else f"{candidate.timestamp_sec:07.1f}s"
    return f"{rank:04d}__score_{candidate.score:.3f}__{candidate.half}__{timestamp}__{candidate.image_path.name}"


def write_csv(path: Path, candidates: list[Candidate]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "rank",
        "score",
        "half",
        "timestamp_sec",
        "edge_density",
        "non_green_ratio",
        "largest_component_ratio",
        "box_area_ratio",
        "box_aspect_ratio",
        "logo_color_ratio",
        "magenta_ratio",
        "center_distance",
        "x1",
        "y1",
        "x2",
        "y2",
        "image_path",
    ]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for rank, candidate in enumerate(candidates, start=1):
            writer.writerow(
                {
                    "rank": rank,
                    "score": round(candidate.score, 6),
                    "half": candidate.half,
                    "timestamp_sec": candidate.timestamp_sec,
                    "edge_density": round(candidate.edge_density, 6),
                    "non_green_ratio": round(candidate.non_green_ratio, 6),
                    "largest_component_ratio": round(candidate.largest_component_ratio, 6),
                    "box_area_ratio": round(candidate.box_area_ratio, 6),
                    "box_aspect_ratio": round(candidate.box_aspect_ratio, 6),
                    "logo_color_ratio": round(candidate.logo_color_ratio, 6),
                    "magenta_ratio": round(candidate.magenta_ratio, 6),
                    "center_distance": round(candidate.center_distance, 6),
                    "x1": candidate.x1,
                    "y1": candidate.y1,
                    "x2": candidate.x2,
                    "y2": candidate.y2,
                    "image_path": candidate.image_path.as_posix(),
                }
            )


def write_contact_sheet(review_images: list[Path], output: Path, cols: int, thumb_width: int) -> None:
    if not review_images:
        return
    thumbs: list[np.ndarray] = []
    for path in review_images:
        image = cv2.imread(str(path))
        if image is None:
            continue
        h, w = image.shape[:2]
        scale = thumb_width / max(w, 1)
        thumb = cv2.resize(image, (thumb_width, int(h * scale)))
        thumbs.append(thumb)
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
    if not args.frames_root.exists():
        raise SystemExit(f"frames root not found: {args.frames_root}")

    frames = collect_frames(args.frames_root, args.stride)
    if not frames:
        raise SystemExit(f"no frames found under: {args.frames_root}")

    candidates: list[Candidate] = []
    for frame in frames:
        candidate = score_frame(frame)
        if candidate is None:
            continue
        if candidate.score < args.min_score:
            continue
        if not args.min_box_area_ratio <= candidate.box_area_ratio <= args.max_box_area_ratio:
            continue
        if candidate.center_distance > args.max_center_distance:
            continue
        if not args.min_box_aspect_ratio <= candidate.box_aspect_ratio <= args.max_box_aspect_ratio:
            continue
        if candidate.logo_color_ratio < args.min_logo_color_ratio:
            continue
        if candidate.magenta_ratio < args.min_magenta_ratio:
            continue
        candidates.append(candidate)

    candidates.sort(key=lambda item: item.score, reverse=True)
    selected = candidates[: max(1, args.top_k)]

    review_dir = args.output_root / "review"
    raw_dir = args.output_root / "raw"
    review_dir.mkdir(parents=True, exist_ok=True)
    if args.copy_originals:
        raw_dir.mkdir(parents=True, exist_ok=True)

    review_paths: list[Path] = []
    for rank, candidate in enumerate(selected, start=1):
        name = output_name(rank, candidate)
        review = draw_review(candidate)
        if review is not None:
            review_path = review_dir / name
            cv2.imwrite(str(review_path), review)
            review_paths.append(review_path)
        if args.copy_originals:
            shutil.copy2(candidate.image_path, raw_dir / name)

    write_csv(args.output_root / "candidates.csv", selected)
    write_contact_sheet(
        review_paths[: min(len(review_paths), args.top_k)],
        args.output_root / "contact_sheet.jpg",
        cols=args.contact_sheet_cols,
        thumb_width=args.contact_sheet_thumb_width,
    )

    print(f"frames scanned: {len(frames)}")
    print(f"candidates above threshold: {len(candidates)}")
    print(f"selected candidates: {len(selected)}")
    print(f"csv: {args.output_root / 'candidates.csv'}")
    print(f"review images: {review_dir}")
    print(f"contact sheet: {args.output_root / 'contact_sheet.jpg'}")


if __name__ == "__main__":
    main()
