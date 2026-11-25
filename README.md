# Student-engagemnt
##
##
##
E
E
Mmbers of the team:
Ivanov Yaromir, Shtyrev Egor, Jbira Kareem

Comunication via Telegram

Project is made to adress the problem of low engagement during exams.

See the [project brief](docs/project_brief.md) for the user, goal, data plan and next actions.

## Lab 02: repeatable person-detection baseline

The pipeline loads and checks the classroom-image sample, applies pretrained
YOLOv8m, calculates annotated-person recall, and automatically saves
[reports/baseline_metrics.json](reports/baseline_metrics.json).
The model is used without additional training.

This first visual experiment uses classroom still images. It does not yet
test the system in exam conditions.

### Setup and run

Tested with Python 3.12 on Windows. From the repository root:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src/baseline_pipeline.py --download
```

The first run downloads dataset version 1 (about 123 MiB). For manual download,
extract the archive so the 481 JPG images are in `data/raw/dataset/images/`
and matching TXT labels are in `data/raw/dataset/labels/`. Dataset background
is in [data/README.md](data/README.md).
After the data is in place, the repeatable baseline command is:

```powershell
.\.venv\Scripts\python.exe src/baseline_pipeline.py
```

To prepare the data without running the model:

```powershell
.\.venv\Scripts\python.exe src/baseline_pipeline.py --prepare-only
```

The first prediction run downloads official `yolov8m.pt` weights (about 50 MiB)
to `models/`. Predictions run on the CPU with image size 640, confidence 0.25
and NMS IoU 0.7, keeping only the COCO `person` class. The 20 resulting images
with predicted boxes are saved in `runs/yolov8m/`. Open them in an image viewer
to inspect the detections. Repeating the command uses the same images, weights,
settings and output folder. Weights and generated images stay outside Git.

The primary metric is annotated-person recall at IoU 0.5: matched annotation
boxes divided by all annotation boxes. For this localization check, the eight
action classes are treated as person locations; original labels stay unchanged.
Predictions are matched in descending confidence order, and each prediction and
annotation can be used only once. Matching IoU 0.5 is separate from NMS IoU 0.7.

This is an initial person-localization result. The model does not recognize
engagement or the eight action classes. The sample is small, frames may be
similar, and person annotations may be incomplete or cover only upper bodies.
No training or parameter search is performed.

On macOS/Linux, create the environment with `python3 -m venv .venv` and use
`.venv/bin/python` in place of `.\.venv\Scripts\python.exe` above.

The command:

1. Loads 20 image/label pairs selected in advance with seed 42.
2. Checks matching JPG/TXT files, image decoding and RGB dimensions, and
   five-column YOLO labels with class IDs 0-7 and normalized coordinates.
3. Creates or reloads `data/evaluation/` and verifies the fixed filenames and
   SHA-256 hashes against `data/evaluation_manifest.json`.
4. Applies COCO-pretrained YOLOv8m to the 20 evaluation images.
5. Calculates annotated-person recall at IoU 0.5.
6. Writes the measured metric, counts, settings and limitation to
   `reports/baseline_metrics.json` automatically.

The [evaluation strategy](docs/split_strategy.md) explains why there is no
training split and records the sample limitations. The manifest is small
metadata kept in Git; images, label files, archives and environments are ignored.

To check reproducibility, a teammate should use a fresh clone and environment,
follow these instructions and confirm that the same 20 files pass validation
and `reports/baseline_metrics.json` is created or updated. This teammate check
has not yet been recorded; the saved report contains the measured local run.

## Lab 03: acceptance decisions

See [project decisions](docs/project_decisions.md) for the baseline decision,
required behavior, acceptance check and planned failure responses.

## Lab 04
## Run the inference demo

Images are read from `dataset/images/` (Kaggle "Classroom Student Engagement
Dataset", v1). Requires `models/yolov8m.pt` — downloaded automatically on first run.

macOS/Linux:
    python3 src/inference_demo.py --input-ref dataset/images/<file>.jpg

Windows PowerShell:
    py src\inference_demo.py --input-ref dataset\images\<file>.jpg
    # use `python` if `py` is not recognized

Output: `reports/inference_demo.jsonl` — one normal record and one
simulated-unavailable record, linked by `request_id`.


## Lab 05

The inference demo validates input requests against config/input_contract.json before running YOLOv8m. It checks input references, formats, dimensions, approved sources and preprocessing identifiers. Requests are assigned a combined status: pass, warning or error. Passing requests proceed to prediction, warnings are routed for review, and errors are rejected.

The three validation scenarios are automatically demonstrated and saved in reports/validation_demo.jsonl. Unit tests are provided in tests/test_input_validation.py to check severity handling and prediction routing.

## Lab 07: containerised inference service

The Lab 06 API in `ait-yolo-service/` is packaged as a Docker image. It keeps
the same input checks, prediction model and JSON responses. Runtime settings
come from `.env`; request evidence is saved in a mounted `reports/` directory
so replacing the container does not remove earlier records.

See [container setup and checks](docs/container_service.md) for the build,
tests, two requests from another computer, evidence check and replacement
commands. `check_service.py` saves both API responses for the defense.

Verified on the team's Ubuntu VM on 25 November 2026: all 8 tests passed
inside Docker, the valid and rejected requests returned HTTP 200 and 400
from another computer, and the journal checksum stayed the same after
container replacement. The demonstration container is stopped; the image
and evidence remain on the VM for the defense.
