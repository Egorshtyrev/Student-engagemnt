# Project brief

## User and situation

University instructors want to understand student engagement during lessons
and exams. Observing every student is difficult. We want to explore whether
classroom images can help teachers review student activity.

## What the system should do

- Input: classroom images from the selected dataset.
- Useful output: images with detected people now; recognition of visible student actions is a possible later step.
- Action or decision after the output: a teacher reviews the results and decides which situations need attention.

## Why AI may help

Students look different and may be partly hidden. AI can learn visual patterns
from examples. Our current pretrained YOLOv8m finds people only. It does not
recognize engagement or the dataset's eight action classes. A person reviews
the output.

## Initial data plan

- Where the data may come from: the [Classroom Student Engagement Dataset on Kaggle](https://www.kaggle.com/datasets/mustafaxgm/classroom-student-engagement-dataset).
- What we can access now: 481 classroom images with YOLO labels; 20 images are reserved for evaluation.
- What still needs confirmation: whether the labels support a useful detection metric and whether classroom images represent exam conditions.

## Three next actions

1. Choose and calculate one metric for person detection.
2. Save the measured result automatically to `reports/baseline_metrics.json`.
3. Ask a teammate to repeat the run from a fresh clone using the README.
