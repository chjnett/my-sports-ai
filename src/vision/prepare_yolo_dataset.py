from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import yaml


CLASSES = ["scoreboard", "overlay", "replay_logo"]


def ensure_dataset_dirs(dataset_root: Path) -> None:
    for relative in [
        "images/train",
        "images/val",
        "labels/train",
        "labels/val",
    ]:
        directory = dataset_root / relative
        directory.mkdir(parents=True, exist_ok=True)
        (directory / ".gitkeep").touch(exist_ok=True)


def write_data_yaml(dataset_root: Path) -> Path:
    payload = {
        "path": "/app/datasets/yolo_broadcast_graphics",
        "train": "images/train",
        "val": "images/val",
        "names": {index: name for index, name in enumerate(CLASSES)},
    }
    output = dataset_root / "data.yaml"
    with output.open("w", encoding="utf-8") as handle:
        yaml.safe_dump(payload, handle, allow_unicode=True, sort_keys=False)
    return output


def collect_frames(frames_root: Path) -> list[Path]:
    return sorted(frames_root.rglob("*.jpg"))


def select_frames(files: list[Path], limit: int, stride: int) -> list[Path]:
    if stride > 1:
        files = files[::stride]
    if limit > 0:
        files = files[:limit]
    return files


def build_output_name(frame: Path, frames_root: Path) -> str:
    relative = frame.relative_to(frames_root).with_suffix("")
    safe = "__".join(relative.parts)
    return f"{safe}.jpg"


def copy_frames(
    frames: list[Path],
    frames_root: Path,
    dataset_root: Path,
    val_every: int,
    create_empty_labels: bool,
) -> tuple[int, int]:
    train_count = 0
    val_count = 0

    for index, frame in enumerate(frames):
        split = "val" if val_every > 0 and index % val_every == 0 else "train"
        output_name = build_output_name(frame, frames_root)
        image_out = dataset_root / "images" / split / output_name
        label_out = dataset_root / "labels" / split / f"{Path(output_name).stem}.txt"

        image_out.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(frame, image_out)

        if create_empty_labels and not label_out.exists():
            label_out.parent.mkdir(parents=True, exist_ok=True)
            label_out.write_text("", encoding="utf-8")

        if split == "val":
            val_count += 1
        else:
            train_count += 1

    return train_count, val_count


def main() -> None:
    parser = argparse.ArgumentParser(description="Prepare YOLO dataset folders and representative frame images.")
    parser.add_argument("--frames-root", required=True, help="Root containing sampled frame folders.")
    parser.add_argument("--dataset-root", default="datasets/yolo_broadcast_graphics", help="YOLO dataset root.")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of frames to copy. Use 0 for all.")
    parser.add_argument("--stride", type=int, default=180, help="Select every Nth frame before applying limit.")
    parser.add_argument("--val-every", type=int, default=5, help="Send every Nth selected frame to val.")
    parser.add_argument("--create-empty-labels", action="store_true", help="Create empty YOLO txt labels.")
    args = parser.parse_args()

    frames_root = Path(args.frames_root)
    dataset_root = Path(args.dataset_root)

    if not frames_root.exists():
        raise SystemExit(f"frames root does not exist: {frames_root}")

    ensure_dataset_dirs(dataset_root)
    data_yaml = write_data_yaml(dataset_root)

    frames = collect_frames(frames_root)
    selected = select_frames(frames, limit=args.limit, stride=max(args.stride, 1))
    train_count, val_count = copy_frames(
        selected,
        frames_root=frames_root,
        dataset_root=dataset_root,
        val_every=args.val_every,
        create_empty_labels=args.create_empty_labels,
    )

    print(f"data yaml: {data_yaml}")
    print(f"found frames: {len(frames)}")
    print(f"selected frames: {len(selected)}")
    print(f"train images: {train_count}")
    print(f"val images: {val_count}")


if __name__ == "__main__":
    main()
