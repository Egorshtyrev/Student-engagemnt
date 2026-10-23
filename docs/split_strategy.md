# Evaluation sample

- We use pretrained YOLOv8m without additional training, so no training split is needed.
- We reserved 20 of the 481 images for evaluation. They were selected once with seed 42. The other 461 images are unused in this run.
- The list is saved in `data/evaluation_manifest.json`. Each run uses the same 20 images and keeps the original labels.
- We do not use this sample to train the model or change its settings.
- Limitation: the sample is small and contains similar frames from the same videos. Classroom images may differ from real exam conditions. If we train later, frames from one video must stay together in one split.
