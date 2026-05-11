"""Compose extracted highlight clips into one mp4."""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compose highlight clips using ffmpeg concat demuxer.")
    parser.add_argument("--clip-plan", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--reencode", action="store_true", help="Re-encode concat output instead of stream copy.")
    return parser.parse_args()


def read_clip_paths(path: Path) -> list[Path]:
    if not path.exists():
        raise SystemExit(f"Clip plan not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(
        key=lambda row: (
            int(row.get("half") or 999999),
            float(row.get("clip_start_sec") or 0.0),
            int(row.get("rank") or 999999),
        )
    )
    return [Path(row["output_clip"]) for row in rows if row.get("output_clip")]


def ffmpeg_concat_path(path: Path) -> str:
    return path.resolve().as_posix().replace("'", "'\\''")


def write_concat_list(paths: list[Path], output: Path) -> Path:
    concat_list = output.with_suffix(".concat.txt")
    concat_list.parent.mkdir(parents=True, exist_ok=True)
    with concat_list.open("w", encoding="utf-8") as handle:
        for path in paths:
            handle.write(f"file '{ffmpeg_concat_path(path)}'\n")
    return concat_list


def main() -> None:
    args = parse_args()
    clip_paths = read_clip_paths(args.clip_plan)
    existing = [path for path in clip_paths if path.exists() and path.stat().st_size > 0]
    if not existing:
        raise SystemExit("No extracted clips found to compose.")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    if args.output.exists() and args.output.stat().st_size > 0 and not args.overwrite:
        print(f"skip existing highlight: {args.output}")
        return

    concat_list = write_concat_list(existing, args.output)
    command = [
        args.ffmpeg,
        "-y" if args.overwrite else "-n",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        concat_list.as_posix(),
    ]
    if args.reencode:
        command.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "23", "-c:a", "aac", "-b:a", "128k"])
    else:
        command.extend(["-c", "copy"])
    command.extend(["-movflags", "+faststart", args.output.as_posix()])

    subprocess.run(command, check=True)
    print(f"clips: {len(existing)}/{len(clip_paths)}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
