"""Rank fused highlight candidates with simple evidence-based scoring."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


DEFAULT_NOISE_TOKENS = {
    "CHE",
    "BUR",
    "RUR",
    "CHEBUR",
    "CORN",
    "CORNER",
    "CORNERS",
    "CORNRS",
    "LEGEND",
    "SUPPORT",
    "SUPPOR",
    "BUILDING",
    "BULLDING",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Rank highlight candidates.")
    parser.add_argument("--input", required=True, type=Path, help="Fused highlight candidate CSV.")
    parser.add_argument("--output", required=True, type=Path, help="Ranked candidate CSV.")
    parser.add_argument(
        "--boost-tokens",
        default="",
        help="Comma-separated high-value cue tokens, usually known player names.",
    )
    parser.add_argument("--noise-tokens", default="", help="Extra comma-separated noisy cue tokens.")
    return parser.parse_args()


def parse_int(value: str | None, default: int = 0) -> int:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_float(value: str | None, default: float = 0.0) -> float:
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def parse_tokens(raw: str) -> set[str]:
    return {token.strip().upper() for token in raw.split(",") if token.strip()}


def split_semicolon(raw: str | None) -> list[str]:
    if not raw:
        return []
    return [item.strip().upper() for item in raw.split(";") if item.strip()]


def candidate_score(row: dict[str, str], boost_tokens: set[str], noise_tokens: set[str]) -> tuple[float, list[str]]:
    evidence_types = set(split_semicolon(row.get("evidence_types")))
    cue_texts = split_semicolon(row.get("cue_texts"))
    evidence_count = parse_int(row.get("evidence_count"))
    duration = max(0.0, parse_float(row.get("end_timestamp_sec")) - parse_float(row.get("start_timestamp_sec")))

    score = 0.0
    reasons: list[str] = []

    if "SCORE_CHANGE" in evidence_types:
        score += 100.0
        reasons.append("score_change:+100")
    if "REPLAY_TRANSITION_LOGO" in evidence_types:
        score += 20.0
        reasons.append("replay_transition:+20")
    if "REPLAY_SEGMENT" in evidence_types:
        score += 15.0
        reasons.append("replay_segment:+15")
    if "TEXT_CUE" in evidence_types:
        score += 10.0
        reasons.append("text_cue:+10")
    if "RED_CARD" in evidence_types:
        score += 70.0
        reasons.append("red_card:+70")
    if "YELLOW_CARD" in evidence_types:
        score += 15.0
        reasons.append("yellow_card:+15")
    if "SUBSTITUTION" in evidence_types:
        score += 10.0
        reasons.append("substitution:+10")

    if evidence_types == {"TEXT_CUE"}:
        score -= 30.0
        reasons.append("isolated_text_cue:-30")

    evidence_bonus = min(evidence_count, 8) * 1.5
    if evidence_bonus:
        score += evidence_bonus
        reasons.append(f"evidence_count:+{evidence_bonus:.1f}")

    for token in cue_texts:
        if token in boost_tokens:
            score += 80.0
            reasons.append(f"boost:{token}:+80")
        elif 4 <= len(token) <= 12 and token not in noise_tokens and not any(noise in token for noise in noise_tokens):
            score += 5.0
            reasons.append(f"player_like:{token}:+5")
        if token in noise_tokens or any(noise in token for noise in noise_tokens):
            score -= 8.0
            reasons.append(f"noise:{token}:-8")

    if duration > 90:
        score -= 15.0
        reasons.append("long_span:-15")
    elif duration > 30:
        score -= 5.0
        reasons.append("wide_span:-5")

    return score, reasons


def main() -> None:
    args = parse_args()
    if not args.input.exists():
        raise SystemExit(f"Candidate CSV not found: {args.input}")

    boost_tokens = parse_tokens(args.boost_tokens)
    noise_tokens = set(DEFAULT_NOISE_TOKENS) | parse_tokens(args.noise_tokens)

    with args.input.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        fieldnames = list(reader.fieldnames or [])

    for row in rows:
        score, reasons = candidate_score(row, boost_tokens=boost_tokens, noise_tokens=noise_tokens)
        row["rank_score"] = f"{score:.3f}"
        row["rank_reasons"] = ";".join(reasons)

    rows.sort(
        key=lambda row: (
            -parse_float(row.get("rank_score")),
            str(row.get("half", "")),
            parse_float(row.get("timestamp_sec")),
        )
    )
    for index, row in enumerate(rows, start=1):
        row["rank"] = str(index)

    output_fieldnames = ["rank", "rank_score", *fieldnames, "rank_reasons"]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"input candidates: {len(rows)}")
    print(f"output: {args.output}")
    for row in rows[:10]:
        print(
            f"#{row['rank']} score={row['rank_score']} half={row.get('half')} "
            f"ts={row.get('timestamp_sec')} evidence={row.get('evidence_types')} cues={row.get('cue_texts')}"
        )


if __name__ == "__main__":
    main()
