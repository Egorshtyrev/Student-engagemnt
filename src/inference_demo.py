import argparse
import json
import sys
import time
import uuid
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
MODEL_WEIGHTS = ROOT / "models" / "yolov8m.pt"
EVIDENCE_PATH = ROOT / "reports" / "inference_demo.jsonl"

DEFAULT_IMAGE_DIR = ROOT / "dataset" / "images"

MODEL_VERSION = "baseline-v1"
RULE_VERSION = "decision-v1"

NORMAL_ACTION = "show person count and boxes to operator"
REVIEW_ACTION = "ask operator to inspect the frame"
UNAVAILABLE_ACTION = "use manual inspection"

REVIEW_CONFIDENCE_FLOOR = 0.40

_MODEL = None


def get_model():
    global _MODEL
    if _MODEL is None:
        from ultralytics import YOLO

        MODEL_WEIGHTS.parent.mkdir(parents=True, exist_ok=True)
        _MODEL = YOLO(str(MODEL_WEIGHTS))
        if _MODEL.names.get(0) != "person":
            raise ValueError("Expected COCO person class at index 0.")
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
        f"No image found for {input_ref!r}. Looked in: {DEFAULT_IMAGE_DIR}"
    )


def safe_ref(image_path: Path) -> str:
    try:
        return image_path.resolve().relative_to(ROOT.resolve()).as_posix()
    except ValueError:
        return f"dataset/images/{image_path.name}"


def basic_input_check(image_path: Path) -> None:
    with Image.open(image_path) as image:
        if image.format != "JPEG":
            raise ValueError(f"expected JPEG input: {image_path.name}")
        image.load()
        image.convert("RGB")


def project_predict(image_path: Path) -> dict:
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
    needs_review = person_count == 0 or max(confs, default=0.0) < REVIEW_CONFIDENCE_FLOOR
    return {
        "result": {"person_count": person_count, "boxes": boxes},
        "needs_review": needs_review,
    }


def make_request_id() -> str:
    return uuid.uuid4().hex


def run_normal(image_path: Path, input_ref: str) -> dict:
    request_id = make_request_id()
    started = time.perf_counter()
    try:
        basic_input_check(image_path)
        prediction = project_predict(image_path)
        latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
        if prediction["needs_review"]:
            status, action = "review", REVIEW_ACTION
        else:
            status, action = "ok", NORMAL_ACTION
        return {
            "request_id": request_id,
            "input_ref": input_ref,
            "status": status,
            "result": prediction["result"],
            "model_version": MODEL_VERSION,
            "rule_version": RULE_VERSION,
            "latency_ms": latency_ms,
            "action": action,
            "simulated": False,
        }
    except Exception as error:
        latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
        print(f"  (inference failed: {error})", file=sys.stderr)
        return {
            "request_id": request_id,
            "input_ref": input_ref,
            "status": "unavailable",
            "result": None,
            "model_version": MODEL_VERSION,
            "rule_version": RULE_VERSION,
            "latency_ms": latency_ms,
            "action": UNAVAILABLE_ACTION,
            "simulated": False,
        }


def run_simulated_unavailable(input_ref: str) -> dict:
    started = time.perf_counter()
    latency_ms = round((time.perf_counter() - started) * 1000.0, 2)
    return {
        "request_id": make_request_id(),
        "input_ref": input_ref,
        "status": "unavailable",
        "result": None,
        "model_version": MODEL_VERSION,
        "rule_version": RULE_VERSION,
        "latency_ms": latency_ms,
        "action": UNAVAILABLE_ACTION,
        "simulated": True,
    }


def write_records(records: list) -> None:
    EVIDENCE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVIDENCE_PATH.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def pick_default_image() -> Path:
    if not DEFAULT_IMAGE_DIR.is_dir():
        raise FileNotFoundError(f"Image folder missing: {DEFAULT_IMAGE_DIR}")
    candidates = sorted(p for p in DEFAULT_IMAGE_DIR.iterdir()
                        if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg"})
    if not candidates:
        raise FileNotFoundError(f"No .jpg files in {DEFAULT_IMAGE_DIR}")
    return candidates[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Lab 04 inference demo")
    parser.add_argument(
        "--input-ref",
        help=f"Image path or filename. Default: first .jpg in {DEFAULT_IMAGE_DIR}",
    )
    args = parser.parse_args()

    try:
        if args.input_ref:
            image_path = resolve_image(args.input_ref)
        else:
            image_path = pick_default_image()
    except FileNotFoundError as error:
        print(error, file=sys.stderr)
        return 2

    input_ref = safe_ref(image_path)
    print(f"Running inference demo on: {input_ref}")

    normal = run_normal(image_path, input_ref)
    print(f"  normal attempt   -> status={normal['status']!r} "
          f"({normal['latency_ms']} ms)")

    simulated = run_simulated_unavailable(input_ref)
    print(f"  simulated outage -> status={simulated['status']!r} "
          f"(simulated={simulated['simulated']})")

    write_records([normal, simulated])
    print(f"Wrote 2 records to {EVIDENCE_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())