"""Lab 02, steps 1-3: load, validate and reserve a small evaluation sample."""

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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--download", action="store_true", help="Download and extract the public Kaggle v1 dataset first.")
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
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        print(f"Data preparation failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
