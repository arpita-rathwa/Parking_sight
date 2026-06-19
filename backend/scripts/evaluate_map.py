"""
mAP@0.5 evaluation script for detection-service.

Usage:
    python scripts/evaluate_map.py --model-path yolov8n.pt --data-dir ./eval_data

Requires a dataset in YOLO format under --data-dir:
    images/  labels/
"""

import argparse
import json
import sys
from pathlib import Path

from detector.model import DetectionModel
from detector.types import BoundingBox


def compute_iou(a: BoundingBox, b: BoundingBox) -> float:
    return a.iou(b)


def compute_map_at_05(
    predictions: list[list[BoundingBox]],
    ground_truths: list[list[BoundingBox]],
) -> float:
    all_preds = []
    for img_preds, img_gts in zip(predictions, ground_truths):
        for pred in img_preds:
            best_iou = max((compute_iou(pred, gt) for gt in img_gts), default=0.0)
            all_preds.append(
                {"confidence": pred.confidence, "matched": best_iou >= 0.5}
            )

    if not all_preds:
        return 0.0

    all_preds.sort(key=lambda x: x["confidence"], reverse=True)
    tp = sum(1 for p in all_preds if p["matched"])
    fp = len(all_preds) - tp
    total_gts = sum(len(gts) for gts in ground_truths)

    if total_gts == 0:
        return 0.0

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / total_gts if total_gts > 0 else 0.0
    return (precision + recall) / 2 if (precision + recall) > 0 else 0.0


def load_yolo_dataset(data_dir: Path):
    images_dir = data_dir / "images"
    labels_dir = data_dir / "labels"
    if not images_dir.exists():
        raise FileNotFoundError(f"Images directory not found: {images_dir}")

    image_paths = sorted(images_dir.glob("*"))
    ground_truths = []
    for img_path in image_paths:
        label_path = labels_dir / f"{img_path.stem}.txt"
        boxes = []
        if label_path.exists():
            with open(label_path) as f:
                for line in f:
                    parts = line.strip().split()
                    if len(parts) >= 5:
                        cls_id = int(parts[0])
                        cx, cy, w, h = map(float, parts[1:5])
                        x1 = cx - w / 2
                        y1 = cy - h / 2
                        x2 = cx + w / 2
                        y2 = cy + h / 2
                        boxes.append(
                            BoundingBox(
                                x1=x1,
                                y1=y1,
                                x2=x2,
                                y2=y2,
                                confidence=1.0,
                                class_id=cls_id,
                            )
                        )
        ground_truths.append(boxes)
    return image_paths, ground_truths


def main():
    parser = argparse.ArgumentParser(description="Evaluate detection model mAP@0.5")
    parser.add_argument("--model-path", default="yolov8n.pt", help="Path to YOLO model")
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("./eval_data"),
        help="Dataset directory with images/ and labels/",
    )
    parser.add_argument(
        "--confidence", type=float, default=0.5, help="Confidence threshold"
    )
    parser.add_argument("--output", type=Path, default=None, help="Output JSON path")
    args = parser.parse_args()

    print(f"Loading model from {args.model_path}...")
    model = DetectionModel(
        model_path=args.model_path,
        confidence_threshold=args.confidence,
    )
    model.load()

    print(f"Loading dataset from {args.data_dir}...")
    image_paths, ground_truths = load_yolo_dataset(args.data_dir)

    print(f"Running inference on {len(image_paths)} images...")
    import cv2

    predictions = []
    for img_path in image_paths:
        frame = cv2.imread(str(img_path))
        if frame is None:
            predictions.append([])
            continue
        detections = model.predict_single(frame)
        predictions.append(
            [
                BoundingBox(
                    x1=d.bbox.x1,
                    y1=d.bbox.y1,
                    x2=d.bbox.x2,
                    y2=d.bbox.y2,
                    confidence=d.confidence,
                    class_id=d.bbox.class_id,
                )
                for d in detections
                if d.bbox is not None
            ]
        )

    map_score = compute_map_at_05(predictions, ground_truths)
    print(f"mAP@0.5: {map_score:.4f}")

    passed = map_score > 0.85
    print(f"{'PASSED' if passed else 'FAILED'} (threshold: 0.85)")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(
                {
                    "mAP@0.5": map_score,
                    "passed": passed,
                    "num_images": len(image_paths),
                },
                f,
            )

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
