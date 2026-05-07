"""Render ranked highlight candidates as visual contact sheets."""

from __future__ import annotations

import argparse
import csv
import math
import textwrap
from pathlib import Path

import cv2
import numpy as np


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Render ranked highlight candidate review sheets.")
    parser.add_argument("--candidates", required=True, type=Path, help="Ranked candidate CSV.")
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--context-sec", default="-10,0,10", help="Comma-separated offsets around candidate timestamp.")
    parser.add_argument("--thumb-width", type=int, default=320)
    parser.add_argument("--cols", type=int, default=3)
    return parser.parse_args()


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_offsets(raw: str) -> list[int]:
    offsets = [int(part.strip()) for part in raw.split(",") if part.strip()]
    return offsets or [0]


def format_clock(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    minute = seconds // 60
    second = seconds % 60
    return f"{minute:02d}:{second:02d}"


def match_second(half: str, half_timestamp_sec: float) -> float:
    return half_timestamp_sec if str(half).strip() == "1" else 45 * 60 + half_timestamp_sec


def format_time_label(half: str, half_timestamp_sec: float) -> str:
    match_ts = match_second(half, half_timestamp_sec)
    return f"video={half_timestamp_sec:.1f}s  match={format_clock(match_ts)}"


def load_candidates(path: Path, top_k: int) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Candidate CSV not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: int(row.get("rank", "999999")))
    return rows[:top_k]


def infer_frame_path(source_image: str, timestamp_sec: float) -> Path:
    source = Path(source_image)
    if not source.parent.exists():
        return source
    timestamp_ms = int(round(max(0.0, timestamp_sec) * 1000))
    return source.parent / f"{timestamp_ms:010d}.jpg"


def add_header(image: np.ndarray, lines: list[str]) -> np.ndarray:
    output = image.copy()
    header_h = 30 + 24 * len(lines)
    cv2.rectangle(output, (0, 0), (output.shape[1], header_h), (0, 0, 0), -1)
    y = 26
    for line in lines:
        cv2.putText(output, line[:96], (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.58, (0, 255, 255), 2, cv2.LINE_AA)
        y += 24
    return output


def resize_to_width(image: np.ndarray, width: int) -> np.ndarray:
    h, w = image.shape[:2]
    scale = width / max(w, 1)
    return cv2.resize(image, (width, int(h * scale)))


def make_blank(width: int, height: int, text: str) -> np.ndarray:
    image = np.zeros((height, width, 3), dtype=np.uint8)
    cv2.putText(image, text[:64], (12, height // 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2, cv2.LINE_AA)
    return image


def render_candidate(candidate: dict[str, str], offsets: list[int], thumb_width: int) -> np.ndarray:
    base_ts = parse_float(candidate.get("timestamp_sec"))
    half = candidate.get("half", "")
    source_image = candidate.get("source_image", "")
    images: list[np.ndarray] = []

    for offset in offsets:
        timestamp = max(0.0, base_ts + offset)
        path = infer_frame_path(source_image, timestamp)
        image = cv2.imread(str(path))
        if image is None:
            image = make_blank(1280, 720, f"missing {path.name}")
        image = add_header(image, [f"offset {offset:+d}s  {format_time_label(half, timestamp)}"])
        images.append(resize_to_width(image, thumb_width))

    tile_h = max(image.shape[0] for image in images)
    tile = np.zeros((tile_h, thumb_width * len(images), 3), dtype=np.uint8)
    for index, image in enumerate(images):
        x = index * thumb_width
        tile[: image.shape[0], x : x + image.shape[1]] = image

    meta_lines = [
        f"rank #{candidate.get('rank')}  score={candidate.get('rank_score')}  {candidate.get('candidate_id')}",
        f"half={half}  {format_time_label(half, base_ts)}  evidence={candidate.get('evidence_types')}",
    ]
    cue_text = candidate.get("cue_texts", "")
    if cue_text:
        meta_lines.extend(textwrap.wrap(f"cues={cue_text}", width=100)[:2])
    score_signal = candidate.get("score_signal", "")
    if score_signal:
        meta_lines.append(f"score_signal={score_signal}")

    meta_h = 30 + 24 * len(meta_lines)
    output = np.zeros((meta_h + tile.shape[0], tile.shape[1], 3), dtype=np.uint8)
    y = 26
    for line in meta_lines:
        cv2.putText(output, line[:120], (8, y), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (255, 255, 255), 2, cv2.LINE_AA)
        y += 24
    output[meta_h : meta_h + tile.shape[0], : tile.shape[1]] = tile
    return output


def write_contact_sheet(candidate_images: list[np.ndarray], output: Path, cols: int) -> None:
    if not candidate_images:
        return
    cols = max(1, cols)
    rows = math.ceil(len(candidate_images) / cols)
    cell_w = max(image.shape[1] for image in candidate_images)
    cell_h = max(image.shape[0] for image in candidate_images)
    sheet = np.zeros((rows * cell_h, cols * cell_w, 3), dtype=np.uint8)
    for index, image in enumerate(candidate_images):
        row = index // cols
        col = index % cols
        y = row * cell_h
        x = col * cell_w
        sheet[y : y + image.shape[0], x : x + image.shape[1]] = image
    output.parent.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(output), sheet)


def safe_name(candidate: dict[str, str]) -> str:
    timestamp = str(candidate.get("timestamp_sec", "")).replace(".", "p")
    return f"rank_{int(candidate.get('rank', '0')):03d}__{candidate.get('candidate_id')}__h{candidate.get('half')}__{timestamp}s.jpg"


def main() -> None:
    args = parse_args()
    candidates = load_candidates(args.candidates, args.top_k)
    offsets = parse_offsets(args.context_sec)
    image_dir = args.output_root / "images"
    image_dir.mkdir(parents=True, exist_ok=True)

    rendered: list[np.ndarray] = []
    for candidate in candidates:
        image = render_candidate(candidate, offsets=offsets, thumb_width=args.thumb_width)
        output_path = image_dir / safe_name(candidate)
        cv2.imwrite(str(output_path), image)
        rendered.append(image)

    contact_sheet = args.output_root / "contact_sheet.jpg"
    write_contact_sheet(rendered, contact_sheet, cols=args.cols)

    print(f"candidates: {args.candidates}")
    print(f"top_k: {len(candidates)}")
    print(f"candidate images: {image_dir}")
    print(f"contact sheet: {contact_sheet}")


if __name__ == "__main__":
    main()
