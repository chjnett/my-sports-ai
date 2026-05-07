"""Run the Phase 1 highlight pipeline for a configured match batch."""

from __future__ import annotations

import argparse
import csv
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


DEFAULT_STAGES = [
    "frames",
    "detect",
    "replay",
    "crops",
    "ocr",
    "reparse",
    "smooth",
    "text",
    "fuse",
    "rank",
    "eval",
    "review",
]


@dataclass(frozen=True)
class MatchPaths:
    match_id: str
    match_dir: Path
    frame_dir: Path
    reports_dir: Path
    label_events: Path
    detections: Path
    replay_events: Path
    crop_root: Path
    crop_summary: Path
    ocr_full: Path
    ocr_reparsed: Path
    ocr_smoothed: Path
    score_events: Path
    text_events: Path
    candidates: Path
    ranked_candidates: Path
    score_eval: Path
    candidate_eval: Path
    topk_eval: Path
    topk_details: Path
    review_root: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run configured 5-match Phase 1 batch.")
    parser.add_argument("--config", default="configs/batch_5_matches.yml", type=Path)
    parser.add_argument(
        "--stages",
        default="all",
        help=f"Comma-separated stages or 'all'. Available: {','.join(DEFAULT_STAGES)}",
    )
    parser.add_argument("--skip-existing", action="store_true", help="Skip stages whose output already exists.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--limit-matches", type=int, default=0)
    parser.add_argument("--ocr-device", default="gpu", choices=["gpu", "cpu"])
    parser.add_argument(
        "--continue-on-error",
        action="store_true",
        help="Log a failed match/stage and continue with the next match.",
    )
    return parser.parse_args()


def load_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise SystemExit(f"Batch config not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def parse_stage_list(raw: str) -> list[str]:
    if raw.strip().lower() == "all":
        return list(DEFAULT_STAGES)
    stages = [stage.strip() for stage in raw.split(",") if stage.strip()]
    unknown = [stage for stage in stages if stage not in DEFAULT_STAGES]
    if unknown:
        raise SystemExit(f"Unknown stage(s): {', '.join(unknown)}")
    return stages


def as_path(value: str | Path) -> Path:
    return Path(str(value).replace("\\", "/"))


def paths_for_match(config: dict[str, Any], match: dict[str, Any]) -> MatchPaths:
    match_id = match["id"]
    relative_path = as_path(match["relative_path"])
    data_root = as_path(config["data_root"])
    frames_root = as_path(config["frames_root"])
    output_root = as_path(config["output_root"])
    match_root = output_root / "matches" / match_id

    return MatchPaths(
        match_id=match_id,
        match_dir=data_root / relative_path,
        frame_dir=frames_root / relative_path,
        reports_dir=match_root / "reports",
        label_events=match_root / "reports" / "phase1a_events.csv",
        detections=match_root / "detections" / "graphics.csv",
        replay_events=match_root / "events" / "replay_events.csv",
        crop_root=match_root / "crops",
        crop_summary=match_root / "reports" / "scoreboard_crops.csv",
        ocr_full=match_root / "ocr" / "scoreboard_full.csv",
        ocr_reparsed=match_root / "ocr" / "scoreboard_full_reparsed.csv",
        ocr_smoothed=match_root / "ocr" / "scoreboard_smoothed.csv",
        score_events=match_root / "events" / "score_change_events.csv",
        text_events=match_root / "events" / "text_cues.csv",
        candidates=match_root / "events" / "highlight_candidates.csv",
        ranked_candidates=match_root / "events" / "highlight_candidates_ranked.csv",
        score_eval=match_root / "reports" / "score_change_eval.csv",
        candidate_eval=match_root / "reports" / "highlight_candidate_eval.csv",
        topk_eval=match_root / "reports" / "highlight_topk_eval.csv",
        topk_details=match_root / "reports" / "highlight_topk_eval_details.csv",
        review_root=match_root / "reviews" / "highlight_top5",
    )


def command_for_stage(
    stage: str,
    config: dict[str, Any],
    paths: MatchPaths,
    ocr_device: str,
) -> tuple[list[str], Path | None]:
    py = sys.executable
    if stage == "frames":
        return (
            [
                py,
                "-m",
                "src.phase1a",
                "--match-dir",
                paths.match_dir.as_posix(),
                "--data-root",
                str(config["data_root"]),
                "--output-root",
                str(config["frames_root"]),
                "--quality",
                str(config.get("quality", "720p")),
                "--fps",
                str(config.get("fps", 1.0)),
                "--reports-dir",
                paths.reports_dir.as_posix(),
            ],
            paths.label_events,
        )
    if stage == "detect":
        return (
            [
                py,
                "-m",
                "src.vision.detect_graphics",
                "--model",
                str(config["model"]),
                "--frames-root",
                paths.frame_dir.as_posix(),
                "--output",
                paths.detections.as_posix(),
                "--imgsz",
                str(config.get("imgsz", 1280)),
                "--conf",
                str(config.get("detection_conf", 0.25)),
                "--device",
                str(config.get("device", 0)),
            ],
            paths.detections,
        )
    if stage == "replay":
        return (
            [
                py,
                "-m",
                "src.vision.build_replay_events",
                "--detections",
                paths.detections.as_posix(),
                "--output",
                paths.replay_events.as_posix(),
                "--min-conf",
                str(config.get("replay_logo_min_conf", 0.25)),
                "--merge-gap-sec",
                "3",
                "--min-segment-sec",
                "4",
                "--max-segment-sec",
                "90",
            ],
            paths.replay_events,
        )
    if stage == "crops":
        return (
            [
                py,
                "-m",
                "src.vision.crop_detections",
                "--detections",
                paths.detections.as_posix(),
                "--output-root",
                paths.crop_root.as_posix(),
                "--summary",
                paths.crop_summary.as_posix(),
                "--class-name",
                "scoreboard",
                "--min-conf",
                str(config.get("scoreboard_crop_min_conf", 0.70)),
                "--padding",
                str(config.get("scoreboard_crop_padding", 8)),
                "--best-per-frame",
            ],
            paths.crop_summary,
        )
    if stage == "ocr":
        return (
            [
                py,
                "-m",
                "src.ocr.run_scoreboard_ocr",
                "--crops",
                paths.crop_summary.as_posix(),
                "--output",
                paths.ocr_full.as_posix(),
                "--device",
                ocr_device,
            ],
            paths.ocr_full,
        )
    if stage == "reparse":
        return (
            [
                py,
                "-m",
                "src.ocr.reparse_scoreboard_ocr",
                "--input",
                paths.ocr_full.as_posix(),
                "--output",
                paths.ocr_reparsed.as_posix(),
            ],
            paths.ocr_reparsed,
        )
    if stage == "smooth":
        return (
            [
                py,
                "-m",
                "src.ocr.smooth_scoreboard_ocr",
                "--ocr",
                paths.ocr_reparsed.as_posix(),
                "--output",
                paths.ocr_smoothed.as_posix(),
                "--events-output",
                paths.score_events.as_posix(),
                "--window-sec",
                str(config.get("smoothing_window_sec", 8)),
                "--min-votes",
                str(config.get("smoothing_min_votes", 3)),
            ],
            paths.score_events,
        )
    if stage == "text":
        return (
            [
                py,
                "-m",
                "src.ocr.extract_text_cues",
                "--ocr",
                paths.ocr_reparsed.as_posix(),
                "--output",
                paths.text_events.as_posix(),
                "--team-tokens",
                str(config.get("text_team_tokens", "")),
                "--stopwords",
                str(config.get("text_stopwords", "")),
                "--min-token-length",
                str(config.get("text_min_token_length", 4)),
                "--merge-gap-sec",
                str(config.get("text_merge_gap_sec", 20)),
            ],
            paths.text_events,
        )
    if stage == "fuse":
        return (
            [
                py,
                "-m",
                "src.events.fuse_highlight_candidates",
                "--score-events",
                paths.score_events.as_posix(),
                "--text-events",
                paths.text_events.as_posix(),
                "--replay-events",
                paths.replay_events.as_posix(),
                "--output",
                paths.candidates.as_posix(),
                "--merge-window-sec",
                "30",
            ],
            paths.candidates,
        )
    if stage == "rank":
        return (
            [
                py,
                "-m",
                "src.events.rank_highlight_candidates",
                "--input",
                paths.candidates.as_posix(),
                "--output",
                paths.ranked_candidates.as_posix(),
                "--boost-tokens",
                str(config.get("ranking_boost_tokens", "")),
            ],
            paths.ranked_candidates,
        )
    if stage == "eval":
        return (
            [
                py,
                "-m",
                "src.evaluation.evaluate_topk_candidates",
                "--labels",
                paths.label_events.as_posix(),
                "--candidates",
                paths.ranked_candidates.as_posix(),
                "--output",
                paths.topk_eval.as_posix(),
                "--details-output",
                paths.topk_details.as_posix(),
                "--top-k",
                str(config.get("top_k_values", "1,3,5,10,20")),
                "--tolerances",
                "5,10,30",
            ],
            paths.topk_eval,
        )
    if stage == "review":
        return (
            [
                py,
                "-m",
                "src.events.render_ranked_candidates",
                "--candidates",
                paths.ranked_candidates.as_posix(),
                "--output-root",
                paths.review_root.as_posix(),
                "--top-k",
                str(config.get("review_top_k", 5)),
                "--context-sec=-10,0,10",
                "--thumb-width",
                "320",
                "--cols",
                "1",
            ],
            paths.review_root / "contact_sheet.jpg",
        )
    raise ValueError(f"Unsupported stage: {stage}")


def output_exists(path: Path | None) -> bool:
    if path is None:
        return False
    if path.is_dir():
        return any(path.iterdir())
    return path.exists() and path.stat().st_size > 0


def has_label_file(paths: MatchPaths) -> bool:
    return (paths.match_dir / "Labels-v2.json").exists()


def has_half_videos(paths: MatchPaths) -> bool:
    return any(paths.match_dir.glob("1*.mkv")) and any(paths.match_dir.glob("2*.mkv"))


def run_command(command: list[str], dry_run: bool) -> None:
    printable = " ".join(f'"{part}"' if " " in part else part for part in command)
    print(f"$ {printable}")
    if dry_run:
        return
    subprocess.run(command, check=True)


def count_csv_rows(path: Path) -> int:
    if not path.exists():
        return 0
    with path.open("r", newline="", encoding="utf-8") as handle:
        return max(0, sum(1 for _ in handle) - 1)


def read_topk_recall(path: Path, top_k: str = "5") -> str:
    if not path.exists():
        return ""
    with path.open("r", newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle):
            if row.get("top_k") == top_k:
                return row.get("recall_at_30s", "")
    return ""


def write_batch_summary(config: dict[str, Any], match_paths: list[MatchPaths], statuses: dict[str, str]) -> Path:
    output = as_path(config["output_root"]) / "batch_summary.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "match_id",
        "status",
        "detections",
        "scoreboard_crops",
        "ocr_rows",
        "score_events",
        "text_events",
        "candidates",
        "ranked_candidates",
        "top5_recall_at_30s",
        "review_sheet",
    ]
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for paths in match_paths:
            writer.writerow(
                {
                    "match_id": paths.match_id,
                    "status": statuses.get(paths.match_id, ""),
                    "detections": count_csv_rows(paths.detections),
                    "scoreboard_crops": count_csv_rows(paths.crop_summary),
                    "ocr_rows": count_csv_rows(paths.ocr_full),
                    "score_events": count_csv_rows(paths.score_events),
                    "text_events": count_csv_rows(paths.text_events),
                    "candidates": count_csv_rows(paths.candidates),
                    "ranked_candidates": count_csv_rows(paths.ranked_candidates),
                    "top5_recall_at_30s": read_topk_recall(paths.topk_eval, top_k="5"),
                    "review_sheet": (paths.review_root / "contact_sheet.jpg").as_posix(),
                }
            )
    return output


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    stages = parse_stage_list(args.stages)
    matches = list(config["matches"])
    if args.limit_matches > 0:
        matches = matches[: args.limit_matches]

    all_paths: list[MatchPaths] = []
    statuses: dict[str, str] = {}
    for index, match in enumerate(matches, start=1):
        paths = paths_for_match(config, match)
        all_paths.append(paths)
        statuses[paths.match_id] = "pending"
        print(f"\n=== [{index}/{len(matches)}] {paths.match_id} ===")
        print(f"match_dir: {paths.match_dir}")
        if not paths.match_dir.exists():
            print(f"SKIP missing match directory: {paths.match_dir}")
            statuses[paths.match_id] = "skipped_missing_match_dir"
            continue
        if "frames" in stages and not has_label_file(paths):
            print(f"SKIP missing Labels-v2.json: {paths.match_dir / 'Labels-v2.json'}")
            statuses[paths.match_id] = "skipped_missing_labels"
            continue
        if "frames" in stages and not has_half_videos(paths):
            print(f"SKIP missing half videos under: {paths.match_dir}")
            statuses[paths.match_id] = "skipped_missing_videos"
            continue
        try:
            for stage in stages:
                command, expected_output = command_for_stage(stage, config, paths, ocr_device=args.ocr_device)
                if args.skip_existing and output_exists(expected_output):
                    print(f"skip {stage}: {expected_output}")
                    continue
                print(f"\n[{paths.match_id}] stage: {stage}")
                run_command(command, dry_run=args.dry_run)
            statuses[paths.match_id] = "completed" if not args.dry_run else "dry_run"
        except subprocess.CalledProcessError as exc:
            statuses[paths.match_id] = f"failed_stage_exit_{exc.returncode}"
            print(f"FAILED {paths.match_id}: {exc}")
            if not args.continue_on_error:
                raise

    summary = write_batch_summary(config, all_paths, statuses)
    print(f"\nbatch summary: {summary}")


if __name__ == "__main__":
    main()
