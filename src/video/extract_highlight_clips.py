"""Extract mp4 highlight clips from a clip plan."""

from __future__ import annotations

import argparse
import csv
import subprocess
from pathlib import Path


REPORT_FIELDNAMES = [
    "candidate_id",
    "rank",
    "source_video",
    "clip_start_sec",
    "clip_end_sec",
    "planned_duration_sec",
    "output_clip",
    "exists",
    "file_size_mb",
    "status",
    "error",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Extract highlight clips using ffmpeg.")
    parser.add_argument("--clip-plan", required=True, type=Path)
    parser.add_argument("--report", required=True, type=Path)
    parser.add_argument("--ffmpeg", default="ffmpeg")
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--crf", default="23")
    parser.add_argument("--preset", default="veryfast")
    return parser.parse_args()


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def read_plan(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Clip plan not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def output_status(path: Path) -> tuple[str, str]:
    if not path.exists():
        return "0", "0.000"
    return "1", f"{path.stat().st_size / (1024 * 1024):.3f}"


def extract_clip(row: dict[str, str], args: argparse.Namespace) -> dict[str, str]:
    output = Path(row["output_clip"])
    output.parent.mkdir(parents=True, exist_ok=True)
    source = Path(row["source_video"])
    start = parse_float(row.get("clip_start_sec"))
    end = parse_float(row.get("clip_end_sec"))
    duration = max(0.0, end - start)

    report = {
        "candidate_id": row.get("candidate_id", ""),
        "rank": row.get("rank", ""),
        "source_video": source.as_posix(),
        "clip_start_sec": f"{start:.3f}",
        "clip_end_sec": f"{end:.3f}",
        "planned_duration_sec": f"{duration:.3f}",
        "output_clip": output.as_posix(),
        "exists": "0",
        "file_size_mb": "0.000",
        "status": "pending",
        "error": "",
    }

    if output.exists() and output.stat().st_size > 0 and not args.overwrite:
        exists, size = output_status(output)
        report.update({"exists": exists, "file_size_mb": size, "status": "skipped_existing"})
        return report

    command = [
        args.ffmpeg,
        "-y" if args.overwrite else "-n",
        "-ss",
        f"{start:.3f}",
        "-to",
        f"{end:.3f}",
        "-i",
        source.as_posix(),
        "-map",
        "0:v:0",
        "-map",
        "0:a?",
        "-c:v",
        "libx264",
        "-preset",
        args.preset,
        "-crf",
        args.crf,
        "-c:a",
        "aac",
        "-b:a",
        "128k",
        "-movflags",
        "+faststart",
        output.as_posix(),
    ]

    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        exists, size = output_status(output)
        report.update({"exists": exists, "file_size_mb": size, "status": "ok" if exists == "1" else "missing_output"})
    except subprocess.CalledProcessError as exc:
        exists, size = output_status(output)
        report.update(
            {
                "exists": exists,
                "file_size_mb": size,
                "status": f"failed_exit_{exc.returncode}",
                "error": (exc.stderr or exc.stdout or str(exc))[-500:].replace("\n", " "),
            }
        )
    return report


def main() -> None:
    args = parse_args()
    rows = read_plan(args.clip_plan)
    reports = [extract_clip(row, args) for row in rows]

    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=REPORT_FIELDNAMES)
        writer.writeheader()
        writer.writerows(reports)

    ok = sum(1 for row in reports if row["status"] in {"ok", "skipped_existing"})
    print(f"clip plan: {args.clip_plan}")
    print(f"clips ok: {ok}/{len(reports)}")
    print(f"report: {args.report}")


if __name__ == "__main__":
    main()
