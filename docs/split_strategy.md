# Evaluation sample

## Model and sample

We use COCO-pretrained YOLOv8m without training, so no training split is needed.
We reserved 20 of 481 images once with seed 42. The other 461 are unused.
`data/evaluation_manifest.json` fixes the sample; original labels stay unchanged.
We do not tune the model on these images.

## Evaluation

We measure annotated-person recall: the fraction of annotated boxes matched
to person detections at IoU >= 0.5. Each detection can match one annotation.
The eight action classes count as one person class only for localization
evaluation. Prediction confidence is 0.25; NMS IoU is 0.7.
This measures neither actions nor engagement.

## Limitations and future split

The small sample contains similar frames from the same videos. Classroom
images may differ from exam conditions. Ground-truth annotations may omit
people, so recall covers annotated people only. If we train later, all frames
from one video must stay in the same split.
