from __future__ import annotations

import argparse
import shutil
from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a YOLO detector for broadcast graphics.")
    parser.add_argument("--model", default="yolo11n.pt", help="Base YOLO model, e.g. yolo11n.pt or yolo11s.pt.")
    parser.add_argument("--data", default="datasets/yolo_broadcast_graphics/data.yaml", help="YOLO data.yaml path.")
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--imgsz", type=int, default=1280)
    parser.add_argument("--batch", type=int, default=8)
    parser.add_argument("--project", default="models/yolo/runs")
    parser.add_argument("--name", default="broadcast_graphics_yolo11n_smoke")
    parser.add_argument("--device", default=0, help="CUDA device id, 'cpu', or a comma-separated device list.")
    parser.add_argument("--output-model", help="Optional path to copy best.pt after training.")
    args = parser.parse_args()

    model = YOLO(args.model)
    results = model.train(
        data=args.data,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        project=args.project,
        name=args.name,
        device=args.device,
    )

    save_dir = Path(getattr(results, "save_dir", Path(args.project) / args.name))
    best = save_dir / "weights" / "best.pt"
    print(f"training output: {save_dir}")
    print(f"best model: {best}")

    if args.output_model:
        output = Path(args.output_model)
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(best, output)
        print(f"copied best model to: {output}")


if __name__ == "__main__":
    main()
