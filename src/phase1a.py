from __future__ import annotations

import argparse
from pathlib import Path

from src.data.labels import load_events, write_events_csv
from src.video.frame_sampler import discover_videos, sample_video, write_summary_csv


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Phase 1A: labels parsing + frame sampling.")
    parser.add_argument("--match-dir", required=True, help="SoccerNet match directory.")
    parser.add_argument("--data-root", default="data/spotting", help="Root containing SoccerNet match folders.")
    parser.add_argument("--output-root", default="outputs/frames", help="Frame output root.")
    parser.add_argument("--quality", default="720p", help="Preferred video quality.")
    parser.add_argument("--fps", type=float, default=1.0, help="Sampling FPS.")
    parser.add_argument("--max-seconds", type=float, help="Optional limit for smoke tests.")
    parser.add_argument("--overwrite", action="store_true", help="Overwrite existing sampled frames.")
    parser.add_argument("--reports-dir", default="outputs/reports", help="Report output directory.")
    args = parser.parse_args()

    match_dir = Path(args.match_dir)
    label_file = match_dir / "Labels-v2.json"
    if not label_file.exists():
        raise SystemExit(f"Labels-v2.json not found: {label_file}")

    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    events = load_events(label_file, data_root=args.data_root)
    events_csv = write_events_csv(events, reports_dir / "phase1a_events.csv")

    videos = discover_videos(match_dir, quality=args.quality)
    if not videos:
        raise SystemExit(f"No videos found in match directory: {match_dir}")

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
    summary_csv = write_summary_csv(summaries, reports_dir / "phase1a_frame_sampling_summary.csv")

    print(f"Events: {events_csv} ({len(events)} target events)")
    print(f"Frame summary: {summary_csv}")


if __name__ == "__main__":
    main()
