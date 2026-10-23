# Student-engagemnt
E
E
Mmbers of the team:
Ivanov Yaromir, Shtyrev Egor, Jbira Kareem

Comunication via Telegram

Project is made to adress the problem of low engagement during exams.

See the [project brief](docs/project_brief.md) for the user, goal, data plan and next actions.

## Lab 02: preparation and first model run

This stage loads the chosen classroom-image sample, checks images and YOLO
annotations, and reserves a fixed evaluation sample. Running without `--predict`
only prepares data. The optional `--predict` flag applies COCO-pretrained
YOLOv8m without additional training and saves images with detected people.
A quality metric has not been implemented yet.

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
After the data is in place, the repeatable preparation command is:

```powershell
.\.venv\Scripts\python.exe src/baseline_pipeline.py
```

To apply the pretrained model to the same sample:

```powershell
.\.venv\Scripts\python.exe src/baseline_pipeline.py --predict
```

The first prediction run downloads official `yolov8m.pt` weights (about 50 MiB)
to `models/`. Predictions run on the CPU with image size 640, confidence 0.25
and NMS IoU 0.7, keeping only the COCO `person` class. The 20 resulting images
with predicted boxes are saved in `runs/yolov8m/`. Open them in an image viewer
to inspect the detections. Repeating the command uses the same images, weights,
settings and output folder. Weights and generated images stay outside Git.

YOLOv8m detects people, not the dataset's eight engagement/action classes.
These visual results do not establish engagement or detection accuracy.
No training, parameter search or metric calculation is performed.

On macOS/Linux, create the environment with `python3 -m venv .venv` and use
`.venv/bin/python` in place of `.\.venv\Scripts\python.exe` above.

The command:

1. Loads 20 image/label pairs selected in advance with seed 42.
2. Checks matching JPG/TXT files, image decoding and RGB dimensions, and
   five-column YOLO labels with class IDs 0-7 and normalized coordinates.
3. Creates or reloads `data/evaluation/` and verifies the fixed filenames and
   SHA-256 hashes against `data/evaluation_manifest.json`.

The [evaluation strategy](docs/split_strategy.md) explains why there is no
training split and records the sample limitations. The manifest is small
metadata kept in Git; images, label files, archives and environments are ignored.

To check reproducibility, a teammate should use a fresh clone and environment,
follow these instructions and confirm that the same 20 files pass validation.
This teammate check has not yet been recorded. The remaining Lab 02 steps are
to calculate a suitable metric and automatically write
`reports/baseline_metrics.json`; that file remains an empty placeholder here.
