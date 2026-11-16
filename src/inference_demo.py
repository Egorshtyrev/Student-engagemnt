import json
import sys
import time
import uuid
from pathlib import Path

from PIL import Image

from src.input_validation import (
    load_contract,
    validate_request,
    route_request,
)


ROOT = Path(__file__).resolve().parents[1]

MODEL_WEIGHTS = ROOT / "models" / "yolov8m.pt"

DEFAULT_IMAGE_DIR = ROOT / "dataset" / "images"

CONTRACT_PATH = ROOT / "config" / "input_contract.json"

EVIDENCE_PATH = ROOT / "reports" / "validation_demo.jsonl"

MODEL_VERSION = "baseline-v1"
RULE_VERSION = "decision-v1"

REVIEW_CONFIDENCE_FLOOR = 0.40

PREPROCESSING_ID = "yolov8-ultralytics-default-v1"

_MODEL = None

def get_model():
    global _MODEL

    if _MODEL is None:
        from ultralytics import YOLO

        MODEL_WEIGHTS.parent.mkdir(parents=True, exist_ok=True)

        _MODEL = YOLO(str(MODEL_WEIGHTS))

        if _MODEL.names.get(0) != "person":
            raise ValueError(
                "Expected COCO person class at index 0."
            )

    return _MODEL


def resolve_image(input_ref: str) -> Path:
    candidate = Path(input_ref)

    if candidate.is_absolute() and candidate.is_file():
        return candidate

    relative = ROOT / candidate

    if relative.is_file():
        return relative

    in_default = DEFAULT_IMAGE_DIR / candidate.name

    if in_default.is_file():
        return in_default

    raise FileNotFoundError(
        f"No image found for {input_ref!r}. "
        f"Looked in: {DEFAULT_IMAGE_DIR}"
    )


def safe_ref(image_path: Path) -> str:
    try:
        return image_path.resolve().relative_to(
            ROOT.resolve()
        ).as_posix()

    except ValueError:
        return f"dataset/images/{image_path.name}"


def basic_input_check(image_path: Path) -> None:
    """Check that the referenced image is a readable JPEG."""

    with Image.open(image_path) as image:

        if image.format != "JPEG":
            raise ValueError(
                f"Expected JPEG input: {image_path.name}"
            )

        image.load()
        image.convert("RGB")


def project_predict(image_path: Path) -> dict:
    """Run the original YOLO person-detection model."""

    model = get_model()

    results = model.predict(
        source=str(image_path),
        classes=[0],
        conf=0.25,
        iou=0.7,
        imgsz=640,
        device="cpu",
        batch=1,
        save=False,
        verbose=False,
    )

    result = results[0]

    boxes = result.boxes.xyxy.cpu().tolist()
    confs = result.boxes.conf.cpu().tolist()

    person_count = len(boxes)

    needs_review = (
        person_count == 0
        or max(confs, default=0.0) < REVIEW_CONFIDENCE_FLOOR
    )

    return {
        "result": {
            "person_count": person_count,
            "boxes": boxes,
        },
        "needs_review": needs_review,
    }


def predict_from_request(request: dict) -> dict:
    """Convert the request into the input expected by YOLO."""

    image_path = resolve_image(request["input_ref"])

    basic_input_check(image_path)

    return project_predict(image_path)


def make_request_id() -> str:
    return uuid.uuid4().hex


def get_image_metadata(image_path: Path) -> dict:
    """Read dimensions and image format for request metadata."""

    with Image.open(image_path) as image:

        width, height = image.size

        image_format = image.format.lower()

    return {
        "width": width,
        "height": height,
        "format": image_format,
    }


def create_demo_requests(
    image_path: Path,
    contract: dict,
) -> list[dict]:
    """Create one passing, one error and one warning request."""

    metadata = get_image_metadata(image_path)

    if metadata["format"] == "jpeg" and "jpg" in contract["allowed_formats"]:
        metadata["format"] = "jpg"

    approved_sources = contract["allowed_sources"]

    if not approved_sources:
        raise ValueError(
            "Add at least one approved source to input_contract.json."
        )

    approved_source = approved_sources[0]

    warning_source = "unapproved-demo-source"

    while warning_source in approved_sources:
        warning_source += "-new"

    input_ref = safe_ref(image_path)

    normal_request = {
        "request_id": "lab05-pass-001",
        "input_ref": input_ref,
        "format": metadata["format"],
        "width": metadata["width"],
        "height": metadata["height"],
        "source_id": approved_source,
    }

    error_request = {
        "request_id": "lab05-error-002",
        "input_ref": "",
        "format": metadata["format"],
        "width": metadata["width"],
        "height": metadata["height"],
        "source_id": approved_source,
    }

    warning_request = {
        "request_id": "lab05-warning-003",
        "input_ref": input_ref,
        "format": metadata["format"],
        "width": metadata["width"],
        "height": metadata["height"],
        "source_id": warning_source,
    }

    return [
        normal_request,
        error_request,
        warning_request,
    ]


def process_request(
    request: dict,
    contract: dict,
    runtime_context: dict,
) -> dict:
    """Validate first, then route according to validation status."""

    started = time.perf_counter()

    validation = validate_request(
        request,
        contract,
        runtime_context,
    )

    result = route_request(
        request,
        validation,
        predict_from_request,
    )

    latency_ms = round(
        (time.perf_counter() - started) * 1000.0,
        2,
    )

    result["model_version"] = MODEL_VERSION
    result["rule_version"] = RULE_VERSION
    result["latency_ms"] = latency_ms

    return result


def write_records(records: list) -> None:
    """Write one JSON object per line."""

    EVIDENCE_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with EVIDENCE_PATH.open(
        "w",
        encoding="utf-8",
    ) as handle:

        for record in records:
            handle.write(
                json.dumps(record, ensure_ascii=False) + "\n"
            )


def main() -> int:

    print("\nLAB 05 - EXECUTABLE INPUT ASSURANCE")
    print("-----------------------------------")

    try:
        contract = load_contract(CONTRACT_PATH)

        image_candidates = sorted(
            path
            for path in DEFAULT_IMAGE_DIR.iterdir()
            if path.is_file()
            and path.suffix.lower() in {".jpg", ".jpeg"}
        )

        if not image_candidates:
            raise FileNotFoundError(
                f"No JPEG images found in {DEFAULT_IMAGE_DIR}"
            )

        image_path = image_candidates[0]

        print(f"Demo image: {safe_ref(image_path)}")

        runtime_context = {
            "model_package": MODEL_VERSION,
            "transform_id": PREPROCESSING_ID,
        }

        if contract["transform_id"] != PREPROCESSING_ID:
            raise ValueError(
                "The contract transform_id must match "
                f"{PREPROCESSING_ID!r}."
            )

        requests = create_demo_requests(
            image_path,
            contract,
        )

        records = []

        for request in requests:

            result = process_request(
                request,
                contract,
                runtime_context,
            )

            records.append(result)

            print(
                f"{result['status']} | "
                f"{result['request_id']} | "
                f"{result['action']} | "
                f"prediction_ran={result['prediction_ran']}"
            )

        write_records(records)

        print("-----------------------------------")
        print("Validation demonstration completed.")

        print(
            "Report written to: "
            f"{EVIDENCE_PATH.relative_to(ROOT)}"
        )

        return 0

    except Exception as error:

        print(
            f"Demo failed: {error}",
            file=sys.stderr,
        )

        return 1


if __name__ == "__main__":
    raise SystemExit(main())
