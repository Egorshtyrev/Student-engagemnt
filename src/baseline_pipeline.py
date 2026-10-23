"""Run the repeatable Lab 02 person-detection baseline and save its metric."""

import argparse
import hashlib
import json
import math
import random
import shutil
import sys
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
DATASET = "mustafaxgm/classroom-student-engagement-dataset"
VERSION = 1
SEED = 42
SAMPLE_SIZE = 20
EXPECTED_IMAGES = 481
CLASS_NAMES = [
    "handrise", "look_forward", "read", "sleep",
    "stand", "turn_head", "using_device", "write",
]
MATCH_IOU = 0.5
DATA_DIR = ROOT / "data" / "raw" / "dataset"
EVALUATION_DIR = ROOT / "data" / "evaluation"
MANIFEST = ROOT / "data" / "evaluation_manifest.json"
DOWNLOAD_URL = (
    f"https://www.kaggle.com/api/v1/datasets/download/{DATASET}"
    f"?datasetVersionNumber={VERSION}"
)


def download_dataset():
    """Fetch the public versioned archive; keep all images outside Git."""
    archive = ROOT / "data" / "raw" / "classroom-student-engagement-v1.zip"
    archive.parent.mkdir(parents=True, exist_ok=True)
    if not archive.exists():
        print("Downloading Kaggle dataset v1 (about 123 MiB)...", flush=True)
        request = urllib.request.Request(DOWNLOAD_URL, headers={"User-Agent": "Lab02"})
        temporary = archive.with_suffix(".zip.part")
        with urllib.request.urlopen(request, timeout=120) as response:
            with temporary.open("wb") as target:
                shutil.copyfileobj(response, target)
        if not zipfile.is_zipfile(temporary):
            raise ValueError("Kaggle returned a non-ZIP file. See data/README.md for manual download.")
        temporary.replace(archive)

    # Only extract the two documented folders, without trusting archive paths.
    with zipfile.ZipFile(archive) as dataset_zip:
        for entry in dataset_zip.infolist():
            parts = PurePosixPath(entry.filename).parts
            if (
                entry.is_dir() or len(parts) != 3 or parts[0] != "dataset"
                or parts[1] not in {"images", "labels"} or ".." in parts
            ):
                continue
            destination = (archive.parent / Path(*parts)).resolve()
            if not destination.is_relative_to(archive.parent.resolve()):
                raise ValueError(f"Unsafe archive path: {entry.filename}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            with dataset_zip.open(entry) as source, destination.open("wb") as target:
                shutil.copyfileobj(source, target)


def load_sample():
    """Select the documented sample before inspecting images or model outputs."""
    images_dir = DATA_DIR / "images"
    labels_dir = DATA_DIR / "labels"
    if not images_dir.is_dir() or not labels_dir.is_dir():
        raise ValueError("Missing data/raw/dataset/images or labels. Run with --download or follow data/README.md.")
    images = sorted(images_dir.glob("*.jpg"), key=lambda path: path.name)
    if len(images) != EXPECTED_IMAGES:
        raise ValueError(f"Expected {EXPECTED_IMAGES} JPG images from dataset v1, found {len(images)}.")
    image_stems = {image.stem for image in images}
    label_stems = {label.stem for label in labels_dir.glob("*.txt")}
    if image_stems != label_stems:
        raise ValueError("The dataset must have exactly one matching TXT label file for each JPG image.")
    chosen = sorted(random.Random(SEED).sample(images, SAMPLE_SIZE), key=lambda path: path.name)
    return [(image, labels_dir / f"{image.stem}.txt") for image in chosen]


def validate_pair(image_path, label_path):
    """Decode RGB input and check the five-column normalized YOLO annotation."""
    with Image.open(image_path) as image:
        if image.format != "JPEG":
            raise ValueError(f"Expected JPEG: {image_path.name}")
        image.load()
        rgb = image.convert("RGB")
        width, height = rgb.size
        if width <= 0 or height <= 0 or len(rgb.getbands()) != 3:
            raise ValueError(f"Invalid RGB input shape: {image_path.name}")

    boxes = 0
    # An empty label file is a valid YOLO image with no annotated objects.
    for line_number, line in enumerate(label_path.read_text(encoding="utf-8-sig").splitlines(), 1):
        if not line.strip():
            continue
        fields = line.split()
        location = f"{label_path.name}:{line_number}"
        if len(fields) != 5:
            raise ValueError(f"{location}: expected class_id x_center y_center width height.")
        try:
            class_id = int(fields[0])
            x, y, box_width, box_height = map(float, fields[1:])
        except ValueError as error:
            raise ValueError(f"{location}: invalid numeric annotation.") from error
        if not 0 <= class_id < len(CLASS_NAMES):
            raise ValueError(f"{location}: class_id must be an integer from 0 to 7.")
        coordinates = (x, y, box_width, box_height)
        if not all(math.isfinite(value) for value in coordinates):
            raise ValueError(f"{location}: coordinates must be finite.")
        if not (0 <= x <= 1 and 0 <= y <= 1 and 0 < box_width <= 1 and 0 < box_height <= 1):
            raise ValueError(f"{location}: invalid normalized coordinates or non-positive box size.")
        boxes += 1

    return {
        "image": image_path.name,
        "label": label_path.name,
        "image_sha256": hashlib.sha256(image_path.read_bytes()).hexdigest(),
        "label_sha256": hashlib.sha256(label_path.read_bytes()).hexdigest(),
        "width": width,
        "height": height,
        "channels": 3,
        "annotations": boxes,
    }


def reserve_evaluation(sample, records):
    """Create the fixed manifest, or verify it and load the same sample again."""
    manifest = {
        "dataset": DATASET,
        "dataset_version": VERSION,
        "seed": SEED,
        "sample_size": SAMPLE_SIZE,
        "role": "evaluation_only",
        "classes": CLASS_NAMES,
        "evaluation_dir": "data/evaluation",
        "samples": records,
    }
    if MANIFEST.exists():
        saved_manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if saved_manifest != manifest:
            raise ValueError("The data or selection differs from data/evaluation_manifest.json. Do not overwrite the held-out sample.")

    for folder, expected in (
        (EVALUATION_DIR / "images", {image.name for image, _ in sample}),
        (EVALUATION_DIR / "labels", {label.name for _, label in sample}),
    ):
        folder.mkdir(parents=True, exist_ok=True)
        unexpected = {path.name for path in folder.iterdir()} - expected
        if unexpected:
            raise ValueError(f"Unexpected files in {folder.relative_to(ROOT)}; use the documented evaluation sample only.")
    for image, label in sample:
        shutil.copyfile(image, EVALUATION_DIR / "images" / image.name)
        shutil.copyfile(label, EVALUATION_DIR / "labels" / label.name)
    if not MANIFEST.exists():
        MANIFEST.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def box_iou(first, second):
    """Intersection over union of two original-image xyxy boxes."""
    overlap_width = max(0.0, min(first[2], second[2]) - max(first[0], second[0]))
    overlap_height = max(0.0, min(first[3], second[3]) - max(first[1], second[1]))
    intersection = overlap_width * overlap_height
    first_area = max(0.0, first[2] - first[0]) * max(0.0, first[3] - first[1])
    second_area = max(0.0, second[2] - second[0]) * max(0.0, second[3] - second[1])
    union = first_area + second_area - intersection
    return intersection / union if union > 0 else 0.0


def count_matches(predictions, ground_truth):
    """Match confidence-sorted predictions to the best available annotation."""
    available = set(range(len(ground_truth)))
    matched = 0
    for confidence, prediction in sorted(predictions, key=lambda item: item[0], reverse=True):
        if not available:
            break
        best = max(sorted(available), key=lambda index: box_iou(prediction, ground_truth[index]))
        if box_iou(prediction, ground_truth[best]) >= MATCH_IOU:
            available.remove(best)
            matched += 1
    return matched


def load_person_boxes(label_path, width, height):
    """Use all eight action labels as person locations; keep source TXT intact."""
    boxes = []
    for line in label_path.read_text(encoding="utf-8-sig").splitlines():
        if not line.strip():
            continue
        x, y, box_width, box_height = map(float, line.split()[1:])
        boxes.append([
            (x - box_width / 2) * width, (y - box_height / 2) * height,
            (x + box_width / 2) * width, (y + box_height / 2) * height,
        ])
    return boxes


def predict_people(sample):
    """Apply pretrained weights and measure recall of annotated person boxes."""
    import platform
    import torch
    import ultralytics
    from ultralytics import YOLO

    weights = ROOT / "models" / "yolov8m.pt"
    weights.parent.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(weights))  # Ultralytics downloads its official weights on first run.
    if model.names.get(0) != "person":
        raise ValueError("Expected the COCO-pretrained YOLOv8m person class at index 0.")

    results = model.predict(
        source=str(EVALUATION_DIR / "images"),
        classes=[0],
        conf=0.25,
        iou=0.7,
        imgsz=640,
        device="cpu",
        batch=1,
        stream=True,
        save=True,
        project=str(ROOT / "runs"),
        name="yolov8m",
        exist_ok=True,
        verbose=True,
    )
    image_count = 0
    detection_count = 0
    annotation_count = 0
    matched_count = 0
    expected_names = {image.name for image, _ in sample}
    seen_names = set()
    for result in results:
        name = Path(result.path).name
        if name not in expected_names or name in seen_names:
            raise ValueError(f"Unexpected or repeated prediction image: {name}")
        seen_names.add(name)
        height, width = result.orig_shape
        ground_truth = load_person_boxes(EVALUATION_DIR / "labels" / f"{Path(name).stem}.txt", width, height)
        predictions = list(zip(result.boxes.conf.cpu().tolist(), result.boxes.xyxy.cpu().tolist()))
        matched_count += count_matches(predictions, ground_truth)
        annotation_count += len(ground_truth)
        image_count += 1
        detection_count += len(result.boxes)
    if seen_names != expected_names:
        raise ValueError("The model did not process every image in the evaluation manifest.")
    if annotation_count == 0:
        raise ValueError("Cannot calculate annotated-person recall without any ground-truth boxes.")
    print(f"4. Processed {image_count} images; found {detection_count} person detections.", flush=True)
    recall = matched_count / annotation_count
    report = {
        "experiment": "yolov8m_person_localization_baseline_v1",
        "data": f"{DATASET}, version {VERSION}; {EXPECTED_IMAGES} source images",
        "evaluation": f"{image_count} fixed evaluation images, seed {SEED}; no local training or tuning",
        "model": "COCO-pretrained YOLOv8m, person class only, no additional training",
        "metric": {"name": "annotated_person_recall_at_iou_0_5", "value": round(recall, 6)},
        "counts": {
            "evaluation_images": image_count,
            "annotated_people": annotation_count,
            "matched_annotations": matched_count,
            "missed_annotations": annotation_count - matched_count,
            "person_predictions": detection_count,
        },
        "settings": {"confidence": 0.25, "nms_iou": 0.7, "match_iou": MATCH_IOU, "imgsz": 640, "device": "cpu"},
        "evaluation_method": "All eight action classes treated as person locations only; confidence-descending one-to-one IoU matching",
        "environment": {"python": platform.python_version(), "torch": torch.__version__, "ultralytics": ultralytics.__version__},
        "weights_sha256": hashlib.sha256(weights.read_bytes()).hexdigest(),
        "manifest_sha256": hashlib.sha256(MANIFEST.read_bytes()).hexdigest(),
        "limitation": "Only 20 correlated classroom frames; person annotations may be incomplete and cover upper bodies. This measures localization of annotated people, not engagement or action recognition, and does not establish performance on exams. Overlap with COCO training data is unknown.",
    }
    report_path = ROOT / "reports" / "baseline_metrics.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    print(f"5. Annotated-person recall @ IoU 0.5: {matched_count}/{annotation_count} = {recall:.6f}", flush=True)
    print("6. Saved reports/baseline_metrics.json; prediction images: runs/yolov8m/", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download and extract the public Kaggle v1 dataset first.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--predict", action="store_true", help="Run the full baseline (also the default; kept for compatibility).")
    mode.add_argument("--prepare-only", action="store_true", help="Only prepare the sample; skip inference and metric calculation.")
    args = parser.parse_args()
    try:
        if args.download:
            download_dataset()
        sample = load_sample()
        print(f"1. Loaded {len(sample)} image/label pairs from the documented sample.", flush=True)
        records = [validate_pair(image, label) for image, label in sample]
        print(f"2. Checked JPEG decoding, RGB shape and {sum(record['annotations'] for record in records)} YOLO annotations.", flush=True)
        reserve_evaluation(sample, records)
        print("3. Created/loaded 20 evaluation-only images in data/evaluation/.", flush=True)
        print("Fixed selection and file hashes: data/evaluation_manifest.json", flush=True)
        if not args.prepare_only:
            predict_people(sample)
    except (OSError, ValueError, ImportError, RuntimeError, zipfile.BadZipFile) as error:
        print(f"Pipeline failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
