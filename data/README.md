# Data sample

- Source: [Classroom Student Engagement Dataset](https://www.kaggle.com/datasets/mustafaxgm/classroom-student-engagement-dataset), by MustafaxGM, public Kaggle version 1. Licence: [CC BY-NC 4.0](https://creativecommons.org/licenses/by-nc/4.0/); retain attribution and respect the noncommercial restriction.
- Run `python src/baseline_pipeline.py --download` to obtain version 1. Alternatively, download its ZIP from Kaggle and extract the `dataset` directory into `data/raw/`:

  ```text
  data/raw/dataset/images/*.jpg
  data/raw/dataset/labels/*.txt
  ```

- The archive contains 481 JPG images and 481 matching YOLO label files. IDs are `0 handrise`, `1 look_forward`, `2 read`, `3 sleep`, `4 stand`, `5 turn_head`, `6 using_device`, `7 write`. Preserve these labels. The supplied YAML has unusable train/valid/test paths; use the folders above.
- The pipeline checks image decoding, RGB input, matching files and five-column YOLO labels with valid class IDs and finite normalized boxes.
- Raw files and copied files in `data/evaluation/` are not committed. `data/evaluation_manifest.json` records the fixed sample and checksums. This stage prepares data only; it produces no model predictions or metric.
