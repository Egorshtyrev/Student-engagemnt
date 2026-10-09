# Evaluation sample

- This stage only loads, validates and prepares data. Planned YOLOv8m uses pretrained weights without additional training, so no training split is needed.
- Before any inference or tuning, sort the 481 image paths, select 20 with `random.Random(42).sample`, and sort the selection. Reserve all 20 for evaluation; preserve the eight original annotation classes.
- Commit `data/evaluation_manifest.json` with selected filenames, image/label SHA-256 checksums and selection parameters. Later runs load that manifest and verify the same source files. Copy the selected images and labels into `data/evaluation/`; these data files remain outside Git.
- Selected filenames indicate eight source-video groups, with multiple frames from some groups. This small classroom sample does not represent exam footage. COCO overlap is unconfirmed. Do not tune on it; future training and evaluation must keep source-video groups separate.
