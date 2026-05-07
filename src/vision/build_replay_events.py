"""Build replay transition and segment events from detection CSV."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Detection:
    half: int
    timestamp_sec: float
    confidence: float
    x1: float
    y1: float
    x2: float
    y2: float
    image_path: str


@dataclass(frozen=True)
class Transition:
    half: int
    start_sec: float
    end_sec: float
    peak_sec: float
    peak_confidence: float
    count: int
    image_path: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert replay_logo detections into replay events.")
    parser.add_argument("--detections", required=True, type=Path, help="Detection CSV path.")
    parser.add_argument("--output", required=True, type=Path, help="Output replay events CSV path.")
    parser.add_argument("--class-name", default="replay_logo")
    parser.add_argument("--min-conf", type=float, default=0.50)
    parser.add_argument(
        "--merge-gap-sec",
        type=float,
        default=3.0,
        help="Detections within this gap become one transition event.",
    )
    parser.add_argument(
        "--min-segment-sec",
        type=float,
        default=4.0,
        help="Minimum gap between two transition events to create a replay segment.",
    )
    parser.add_argument(
        "--max-segment-sec",
        type=float,
        default=45.0,
        help="Maximum gap between two transition events to create a replay segment.",
    )
    return parser.parse_args()


def load_detections(path: Path, class_name: str, min_conf: float) -> list[Detection]:
    detections: list[Detection] = []
    with path.open("r", newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            if row["class_name"] != class_name:
                continue
            confidence = float(row["confidence"])
            if confidence < min_conf:
                continue
            detections.append(
                Detection(
                    half=int(float(row["half"])),
                    timestamp_sec=float(row["timestamp_sec"]),
                    confidence=confidence,
                    x1=float(row["x1"]),
                    y1=float(row["y1"]),
                    x2=float(row["x2"]),
                    y2=float(row["y2"]),
                    image_path=row["image_path"],
                )
            )
    return sorted(detections, key=lambda item: (item.half, item.timestamp_sec, -item.confidence))


def merge_transitions(detections: list[Detection], merge_gap_sec: float) -> list[Transition]:
    if not detections:
        return []

    groups: list[list[Detection]] = []
    current: list[Detection] = [detections[0]]
    for detection in detections[1:]:
        previous = current[-1]
        same_half = detection.half == previous.half
        close = detection.timestamp_sec - previous.timestamp_sec <= merge_gap_sec
        if same_half and close:
            current.append(detection)
        else:
            groups.append(current)
            current = [detection]
    groups.append(current)

    transitions: list[Transition] = []
    for group in groups:
        peak = max(group, key=lambda item: item.confidence)
        transitions.append(
            Transition(
                half=group[0].half,
                start_sec=min(item.timestamp_sec for item in group),
                end_sec=max(item.timestamp_sec for item in group),
                peak_sec=peak.timestamp_sec,
                peak_confidence=peak.confidence,
                count=len(group),
                image_path=peak.image_path,
            )
        )
    return transitions


def write_events(
    output: Path,
    transitions: list[Transition],
    min_segment_sec: float,
    max_segment_sec: float,
) -> tuple[int, int]:
    output.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "event_type",
        "half",
        "start_sec",
        "end_sec",
        "peak_sec",
        "duration_sec",
        "confidence",
        "count",
        "source",
        "image_path",
    ]
    transition_count = 0
    segment_count = 0
    with output.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()

        for transition in transitions:
            transition_count += 1
            writer.writerow(
                {
                    "event_type": "replay_transition_logo",
                    "half": transition.half,
                    "start_sec": round(transition.start_sec, 3),
                    "end_sec": round(transition.end_sec, 3),
                    "peak_sec": round(transition.peak_sec, 3),
                    "duration_sec": round(transition.end_sec - transition.start_sec, 3),
                    "confidence": round(transition.peak_confidence, 6),
                    "count": transition.count,
                    "source": "detector",
                    "image_path": transition.image_path,
                }
            )

        for first, second in zip(transitions, transitions[1:]):
            if first.half != second.half:
                continue
            start_sec = first.end_sec
            end_sec = second.start_sec
            duration = end_sec - start_sec
            if min_segment_sec <= duration <= max_segment_sec:
                segment_count += 1
                writer.writerow(
                    {
                        "event_type": "replay_segment",
                        "half": first.half,
                        "start_sec": round(start_sec, 3),
                        "end_sec": round(end_sec, 3),
                        "peak_sec": "",
                        "duration_sec": round(duration, 3),
                        "confidence": round(min(first.peak_confidence, second.peak_confidence), 6),
                        "count": first.count + second.count,
                        "source": "paired_transition_logos",
                        "image_path": "",
                    }
                )

    return transition_count, segment_count


def main() -> None:
    args = parse_args()
    if not args.detections.exists():
        raise SystemExit(f"Detection CSV not found: {args.detections}")

    detections = load_detections(args.detections, args.class_name, args.min_conf)
    transitions = merge_transitions(detections, args.merge_gap_sec)
    transition_count, segment_count = write_events(
        args.output,
        transitions,
        min_segment_sec=args.min_segment_sec,
        max_segment_sec=args.max_segment_sec,
    )

    print(f"detections: {args.detections}")
    print(f"input replay detections: {len(detections)}")
    print(f"transition events: {transition_count}")
    print(f"replay segments: {segment_count}")
    print(f"output: {args.output}")


if __name__ == "__main__":
    main()
