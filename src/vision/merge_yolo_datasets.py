"""Merge YOLO datasets into a single training dataset."""

from __future__ import annotations

import argparse
import shutil
from pathlib import Path


CLASSES = {
    0: "scoreboard",
    1: "overlay",
    2: "replay_logo",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Merge multiple YOLO dataset roots.")
    parser.add_argument(
        "--sources",
        nargs="+",
        required=True,
        type=Path,
        help="Source YOLO dataset roots.",
    )
    parser.add_argument(
        "--output-root",
        required=True,
        type=Path,
        help="Merged YOLO dataset root.",
    )
    parser.add_argument(
        "--pseudo-to-train-only",
        action="store_true",
        help="Put any source with 'pseudo' in its folder name into train only.",
    )
    parser.add_argument("--overwrite", action="store_true")
    return parser.parse_args()


def ensure_dirs(root: Path) -> None:
    for split in ["train", "val"]:
        (root / "images" / split).mkdir(parents=True, exist_ok=True)
        (root / "labels" / split).mkdir(parents=True, exist_ok=True)


def write_data_yaml(root: Path) -> None:
    lines = [
        f"path: /app/{root.as_posix()}",
        "train: images/train",
        "val: images/val",
        "names:",
    ]
    for class_id, name in CLASSES.items():
        lines.append(f"  {class_id}: {name}")
    lines.append("")
    (root / "data.yaml").write_text("\n".join(lines), encoding="utf-8")


def split_targets(source: Path, split: str, pseudo_to_train_only: bool) -> list[str]:
    if pseudo_to_train_only and "pseudo" in source.name.lower():
        return ["train"]
    return [split]


def copy_split(source: Path, output_root: Path, split: str, pseudo_to_train_only: bool) -> tuple[int, int]:
    image_dir = source / "images" / split
    label_dir = source / "labels" / split
    if not image_dir.exists():
        return 0, 0

    copied_images = 0
    copied_labels = 0
    source_prefix = source.name.replace(" ", "_")

    for image_path in sorted(image_dir.glob("*.jpg")):
        label_path = label_dir / f"{image_path.stem}.txt"
        for target_split in split_targets(source, split, pseudo_to_train_only):
            target_stem = f"{source_prefix}__{split}__{image_path.stem}"
            target_image = output_root / "images" / target_split / f"{target_stem}{image_path.suffix.lower()}"
            target_label = output_root / "labels" / target_split / f"{target_stem}.txt"

            shutil.copy2(image_path, target_image)
            copied_images += 1
            if label_path.exists():
                shutil.copy2(label_path, target_label)
            else:
                target_label.write_text("", encoding="utf-8")
            copied_labels += 1

    return copied_images, copied_labels


def main() -> None:
    args = parse_args()
    if args.output_root.exists() and args.overwrite:
        shutil.rmtree(args.output_root)
    ensure_dirs(args.output_root)

    total_images = 0
    total_labels = 0
    for source in args.sources:
        if not source.exists():
            raise SystemExit(f"Source not found: {source}")
        for split in ["train", "val"]:
            images, labels = copy_split(
                source=source,
                output_root=args.output_root,
                split=split,
                pseudo_to_train_only=args.pseudo_to_train_only,
            )
            total_images += images
            total_labels += labels
            if images or labels:
                print(f"{source} {split}: images={images}, labels={labels}")

    write_data_yaml(args.output_root)
    print(f"merged dataset: {args.output_root}")
    print(f"total images: {total_images}")
    print(f"total labels: {total_labels}")
    print(f"data yaml: {args.output_root / 'data.yaml'}")


if __name__ == "__main__":
    main()
