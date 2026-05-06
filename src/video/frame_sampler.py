from __future__ import annotations

import argparse
import csv
import re
from dataclasses import asdict, dataclass
from pathlib import Path

import cv2
from tqdm import tqdm


VIDEO_NAME_RE = re.compile(r"^(?P<half>[12])(?:_(?P<quality>\d+p))?\.(mkv|mp4)$", re.IGNORECASE)


@dataclass(frozen=True)
class SamplingSummary:
    video_path: str
    output_dir: str
    match_id: str
    half: int
    source_fps: float
    source_frame_count: int
    duration_sec: float
    sample_fps: float
    saved_frames: int
    skipped_frames: int


def sanitize_path_part(value: str) -> str:
    value = value.replace("\\", "/").strip("/")
    value = re.sub(r"[^A-Za-z0-9가-힣._/\- ]+", "_", value)
    value = re.sub(r"\s+", " ", value)
    return value


def infer_half(video_path: Path) -> int:
    match = VIDEO_NAME_RE.match(video_path.name)
    if not match:
        raise ValueError(f"Cannot infer half from video filename: {video_path.name}")
    return int(match.group("half"))


def infer_match_id(video_path: Path, data_root: Path) -> str:
    match_dir = video_path.parent
    try:
        return match_dir.relative_to(data_root).as_posix()
    except ValueError:
        return match_dir.name


def discover_videos(match_dir: Path, quality: str = "720p") -> list[Path]:
    preferred = [match_dir / f"1_{quality}.mkv", match_dir / f"2_{quality}.mkv"]
    videos = [path for path in preferred if path.exists()]
    if videos:
        return videos

    fallback_names = ["1.mkv", "2.mkv", "1_224p.mkv", "2_224p.mkv", "1_720p.mkv", "2_720p.mkv"]
    return [match_dir / name for name in fallback_names if (match_dir / name).exists()]


def sample_video(
    video_path: str | Path,
    output_root: str | Path = "outputs/frames",
    data_root: str | Path = "data/spotting",
    sample_fps: float = 1.0,
    max_seconds: float | None = None,
    image_ext: str = "jpg",
    jpeg_quality: int = 90,
    overwrite: bool = False,
) -> SamplingSummary:
    video = Path(video_path)
    root = Path(data_root)
    match_id = infer_match_id(video, root)
    safe_match_id = sanitize_path_part(match_id)
    half = infer_half(video)
    out_dir = Path(output_root) / safe_match_id / f"half_{half}"
    out_dir.mkdir(parents=True, exist_ok=True)

    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError(f"Could not open video: {video}")

    source_fps = float(capture.get(cv2.CAP_PROP_FPS) or 0.0)
    source_frame_count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT) or 0)
    if source_fps <= 0:
        capture.release()
        raise RuntimeError(f"Could not read FPS from video: {video}")

    duration_sec = source_frame_count / source_fps if source_frame_count else 0.0
    end_sec = min(duration_sec, max_seconds) if max_seconds else duration_sec
    interval_sec = 1.0 / sample_fps
    saved = 0
    skipped = 0
    timestamp_sec = 0.0
    expected_samples = int(end_sec / interval_sec) + 1 if end_sec > 0 else 0

    encode_params = []
    if image_ext.lower() in {"jpg", "jpeg"}:
        encode_params = [int(cv2.IMWRITE_JPEG_QUALITY), int(jpeg_quality)]

    with tqdm(
        total=expected_samples,
        desc=f"Sampling half {half}",
        unit="frame",
        dynamic_ncols=True,
    ) as progress:
        while timestamp_sec <= end_sec:
            timestamp_ms = int(round(timestamp_sec * 1000))
            frame_path = out_dir / f"{timestamp_ms:010d}.{image_ext}"

            if frame_path.exists() and not overwrite:
                skipped += 1
                timestamp_sec += interval_sec
                progress.update(1)
                continue

            capture.set(cv2.CAP_PROP_POS_MSEC, timestamp_sec * 1000.0)
            ok, frame = capture.read()
            if not ok:
                break

            cv2.imwrite(str(frame_path), frame, encode_params)
            saved += 1
            timestamp_sec += interval_sec
            progress.update(1)

    capture.release()

    return SamplingSummary(
        video_path=video.as_posix(),
        output_dir=out_dir.as_posix(),
        match_id=match_id,
        half=half,
        source_fps=source_fps,
        source_frame_count=source_frame_count,
        duration_sec=duration_sec,
        sample_fps=sample_fps,
        saved_frames=saved,
        skipped_frames=skipped,
    )


def write_summary_csv(summaries: list[SamplingSummary], output_path: str | Path) -> Path:
    out = Path(output_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "video_path",
        "output_dir",
        "match_id",
        "half",
        "source_fps",
        "source_frame_count",
        "duration_sec",
        "sample_fps",
        "saved_frames",
        "skipped_frames",
    ]
    with out.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for summary in summaries:
            writer.writerow(asdict(summary))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description="Sample SoccerNet match videos at a fixed FPS.")
    parser.add_argument("--video", help="Specific video file to sample.")
    parser.add_argument("--match-dir", help="Match directory containing half videos.")
    parser.add_argument("--data-root", default="data/spotting", help="Root containing SoccerNet match folders.")
    parser.add_argument("--output-root", default="outputs/frames", help="Frame output root.")
    parser.add_argument("--summary", default="outputs/reports/frame_sampling_summary.csv", help="CSV summary path.")
    parser.add_argument("--fps", type=float, default=1.0, help="Sampling FPS.")
    parser.add_argument("--quality", default="720p", help="Preferred SoccerNet quality when using --match-dir.")
    parser.add_argument("--max-seconds", type=float, help="Optional limit for quick smoke tests.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing sampled frames.")
    args = parser.parse_args()

    if not args.video and not args.match_dir:
        raise SystemExit("Pass either --video or --match-dir.")

    if args.video:
        videos = [Path(args.video)]
    else:
        videos = discover_videos(Path(args.match_dir), quality=args.quality)
        if not videos:
            raise SystemExit(f"No videos found in match directory: {args.match_dir}")

    summaries = [
        sample_video(
            video,
            output_root=args.output_root,
            data_root=args.data_root,
            sample_fps=args.fps,
            max_seconds=args.max_seconds,
            overwrite=args.overwrite,
        )
        for video in videos
    ]

    summary_path = write_summary_csv(summaries, args.summary)
    total_saved = sum(summary.saved_frames for summary in summaries)
    total_skipped = sum(summary.skipped_frames for summary in summaries)
    print(f"Sampled {len(summaries)} video(s), wrote {total_saved} frame(s), skipped {total_skipped} existing frame(s).")
    print(f"Summary: {summary_path}")


if __name__ == "__main__":
    main()
