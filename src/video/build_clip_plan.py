"""Build a clip extraction plan from ranked highlight candidates."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

import cv2


FIELDNAMES = [
    "match_id",
    "candidate_id",
    "rank",
    "rank_score",
    "half",
    "candidate_video_sec",
    "candidate_match_clock",
    "clip_start_sec",
    "clip_end_sec",
    "clip_duration_sec",
    "source_video",
    "output_clip",
    "evidence_types",
    "score_signal",
    "cue_texts",
    "clip_reason",
    "merged_candidate_ids",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build highlight clip plan from ranked candidates.")
    parser.add_argument("--candidates", required=True, type=Path, help="Ranked highlight candidates CSV.")
    parser.add_argument("--match-dir", required=True, type=Path, help="SoccerNet match directory.")
    parser.add_argument("--output", required=True, type=Path, help="Output clip_plan.csv.")
    parser.add_argument("--clips-dir", required=True, type=Path, help="Directory where clips will be written.")
    parser.add_argument("--match-id", default="", help="Match id to write into the plan.")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--min-rank-score", type=float, default=0.0)
    parser.add_argument("--score-pre-sec", type=float, default=40.0)
    parser.add_argument("--score-post-sec", type=float, default=20.0)
    parser.add_argument("--text-pre-sec", type=float, default=25.0)
    parser.add_argument("--text-post-sec", type=float, default=15.0)
    parser.add_argument("--replay-pre-sec", type=float, default=45.0)
    parser.add_argument("--replay-post-sec", type=float, default=5.0)
    parser.add_argument("--card-pre-sec", type=float, default=25.0)
    parser.add_argument("--card-post-sec", type=float, default=25.0)
    parser.add_argument("--min-duration-sec", type=float, default=20.0)
    parser.add_argument("--max-duration-sec", type=float, default=75.0)
    parser.add_argument("--merge-overlap-ratio", type=float, default=0.50)
    parser.add_argument("--merge-gap-sec", type=float, default=30.0)
    return parser.parse_args()


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_int(value: str | None, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def format_clock(seconds: float) -> str:
    seconds = max(0, int(round(seconds)))
    return f"{seconds // 60:02d}:{seconds % 60:02d}"


def match_clock(half: str, half_sec: float) -> str:
    match_sec = half_sec if str(half).strip() == "1" else 45 * 60 + half_sec
    return format_clock(match_sec)


def split_evidence(raw: str | None) -> set[str]:
    return {part.strip().lower() for part in str(raw or "").split(";") if part.strip()}


def read_candidates(path: Path, top_k: int, min_rank_score: float) -> list[dict[str, str]]:
    if not path.exists():
        raise SystemExit(f"Candidate CSV not found: {path}")
    with path.open("r", newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    rows.sort(key=lambda row: parse_int(row.get("rank"), 999999))
    filtered = [row for row in rows if parse_float(row.get("rank_score")) >= min_rank_score]
    return filtered[:top_k]


def find_half_video(match_dir: Path, half: str) -> Path:
    patterns = [f"{half}_720p.mkv", f"{half}.mkv", f"{half}_*.mkv"]
    for pattern in patterns:
        matches = sorted(match_dir.glob(pattern))
        if matches:
            return matches[0]
    raise SystemExit(f"Half video not found for half={half}: {match_dir}")


def video_duration(path: Path) -> float:
    cap = cv2.VideoCapture(str(path))
    if not cap.isOpened():
        return 0.0
    fps = cap.get(cv2.CAP_PROP_FPS) or 0.0
    frames = cap.get(cv2.CAP_PROP_FRAME_COUNT) or 0.0
    cap.release()
    if fps <= 0:
        return 0.0
    return frames / fps


def clamp_interval(start: float, end: float, duration: float) -> tuple[float, float]:
    if duration > 0:
        start = min(max(0.0, start), duration)
        end = min(max(0.0, end), duration)
    else:
        start = max(0.0, start)
        end = max(start, end)
    if end < start:
        start, end = end, start
    return start, end


def enforce_duration(start: float, end: float, target: float, min_duration: float, max_duration: float, video_duration_sec: float) -> tuple[float, float]:
    duration = end - start
    if duration < min_duration:
        grow = (min_duration - duration) / 2
        start -= grow
        end += grow
    duration = end - start
    if duration > max_duration:
        start = target - max_duration / 2
        end = target + max_duration / 2
    return clamp_interval(start, end, video_duration_sec)


def clip_bounds(row: dict[str, str], args: argparse.Namespace, duration: float) -> tuple[float, float, str]:
    evidence = split_evidence(row.get("evidence_types"))
    ts = parse_float(row.get("timestamp_sec"))
    start = parse_float(row.get("start_timestamp_sec"), ts)
    end = parse_float(row.get("end_timestamp_sec"), ts)

    if "score_change" in evidence:
        clip_start = ts - args.score_pre_sec
        clip_end = ts + args.score_post_sec
        reason = "score_change_pre_goal_window"
    elif "red_card" in evidence or "yellow_card" in evidence:
        clip_start = ts - args.card_pre_sec
        clip_end = ts + args.card_post_sec
        reason = "card_event_window"
    elif "replay_transition_logo" in evidence:
        anchor = min(ts, start, end)
        clip_start = anchor - args.replay_pre_sec
        clip_end = anchor + args.replay_post_sec
        reason = "pre_replay_transition_window"
    elif "replay_segment" in evidence:
        anchor = min(ts, start, end)
        clip_start = anchor - args.replay_pre_sec
        clip_end = anchor + args.replay_post_sec
        reason = "pre_replay_segment_window"
    else:
        clip_start = ts - args.text_pre_sec
        clip_end = ts + args.text_post_sec
        reason = "text_cue_pre_context_window"

    clip_start, clip_end = enforce_duration(
        clip_start,
        clip_end,
        target=ts,
        min_duration=args.min_duration_sec,
        max_duration=args.max_duration_sec,
        video_duration_sec=duration,
    )
    return clip_start, clip_end, reason


def overlap_ratio(a: dict[str, str], b: dict[str, str]) -> float:
    a_start = parse_float(a["clip_start_sec"])
    a_end = parse_float(a["clip_end_sec"])
    b_start = parse_float(b["clip_start_sec"])
    b_end = parse_float(b["clip_end_sec"])
    overlap = max(0.0, min(a_end, b_end) - max(a_start, b_start))
    shorter = max(0.001, min(a_end - a_start, b_end - b_start))
    return overlap / shorter


def should_merge(a: dict[str, str], b: dict[str, str], overlap_threshold: float, gap_sec: float) -> bool:
    if a["half"] != b["half"]:
        return False
    if overlap_ratio(a, b) >= overlap_threshold:
        return True
    a_start = parse_float(a["clip_start_sec"])
    a_end = parse_float(a["clip_end_sec"])
    b_start = parse_float(b["clip_start_sec"])
    b_end = parse_float(b["clip_end_sec"])
    gap = max(0.0, max(a_start, b_start) - min(a_end, b_end))
    return gap <= gap_sec


def merge_rows(base: dict[str, str], incoming: dict[str, str]) -> dict[str, str]:
    start = min(parse_float(base["clip_start_sec"]), parse_float(incoming["clip_start_sec"]))
    end = max(parse_float(base["clip_end_sec"]), parse_float(incoming["clip_end_sec"]))
    base["clip_start_sec"] = f"{start:.3f}"
    base["clip_end_sec"] = f"{end:.3f}"
    base["clip_duration_sec"] = f"{end - start:.3f}"

    evidence = sorted(split_evidence(base["evidence_types"]) | split_evidence(incoming["evidence_types"]))
    base["evidence_types"] = ";".join(evidence)
    if not base["score_signal"] and incoming["score_signal"]:
        base["score_signal"] = incoming["score_signal"]
    cues = {part for part in base["cue_texts"].split(";") if part} | {part for part in incoming["cue_texts"].split(";") if part}
    base["cue_texts"] = ";".join(sorted(cues))
    ids = {part for part in base["merged_candidate_ids"].split(";") if part} | {incoming["candidate_id"]}
    base["merged_candidate_ids"] = ";".join(sorted(ids))
    base["clip_reason"] = f"{base['clip_reason']};merged:{incoming['candidate_id']}"
    return base


def merge_plan(rows: list[dict[str, str]], args: argparse.Namespace) -> list[dict[str, str]]:
    merged: list[dict[str, str]] = []
    for row in rows:
        target = next((existing for existing in merged if should_merge(existing, row, args.merge_overlap_ratio, args.merge_gap_sec)), None)
        if target is None:
            merged.append(row)
        else:
            merge_rows(target, row)
    return merged


def safe_clip_name(row: dict[str, str]) -> str:
    rank = parse_int(row.get("rank"))
    clock = row.get("candidate_match_clock", "00:00").replace(":", "m") + "s"
    return f"rank_{rank:03d}__{row.get('candidate_id')}__h{row.get('half')}__{clock}.mp4"


def build_rows(args: argparse.Namespace) -> list[dict[str, str]]:
    candidates = read_candidates(args.candidates, args.top_k, args.min_rank_score)
    video_cache: dict[str, tuple[Path, float]] = {}
    rows: list[dict[str, str]] = []

    for candidate in candidates:
        half = str(candidate.get("half", "")).strip()
        if half not in video_cache:
            source_video = find_half_video(args.match_dir, half)
            video_cache[half] = (source_video, video_duration(source_video))
        source_video, duration = video_cache[half]
        start, end, reason = clip_bounds(candidate, args, duration)
        ts = parse_float(candidate.get("timestamp_sec"))
        row = {
            "match_id": args.match_id,
            "candidate_id": candidate.get("candidate_id", ""),
            "rank": candidate.get("rank", ""),
            "rank_score": candidate.get("rank_score", ""),
            "half": half,
            "candidate_video_sec": f"{ts:.3f}",
            "candidate_match_clock": match_clock(half, ts),
            "clip_start_sec": f"{start:.3f}",
            "clip_end_sec": f"{end:.3f}",
            "clip_duration_sec": f"{end - start:.3f}",
            "source_video": source_video.as_posix(),
            "output_clip": "",
            "evidence_types": candidate.get("evidence_types", ""),
            "score_signal": candidate.get("score_signal", ""),
            "cue_texts": candidate.get("cue_texts", ""),
            "clip_reason": reason,
            "merged_candidate_ids": candidate.get("candidate_id", ""),
        }
        rows.append(row)

    rows = merge_plan(rows, args)
    for row in rows:
        row["output_clip"] = (args.clips_dir / safe_clip_name(row)).as_posix()
    return rows


def main() -> None:
    args = parse_args()
    rows = build_rows(args)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.clips_dir.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)

    print(f"candidates: {args.candidates}")
    print(f"planned clips: {len(rows)}")
    print(f"output: {args.output}")
    for row in rows:
        print(
            f"rank={row['rank']} half={row['half']} clock={row['candidate_match_clock']} "
            f"clip={row['clip_start_sec']}-{row['clip_end_sec']} -> {row['output_clip']}"
        )


if __name__ == "__main__":
    main()
