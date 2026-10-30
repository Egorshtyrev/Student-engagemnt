# Project decisions

## Lab 03 — Acceptance

### Decision after the baseline

Decision: Continue

Reason: The [Lab 02 report](../reports/baseline_metrics.json) records
annotated-person recall of 0.710843 (118 of 166 boxes matched; 48 missed)
on the 20 fixed evaluation images. We will continue person detection with
teacher review. The sample is small, frames may be similar, and annotations
may be incomplete or cover upper bodies. This result does not show action
recognition, engagement, or performance in exam conditions.

The behavior and responses below are requirements for later Labs.

### Required behavior

- Normal input: a readable classroom JPEG with visible students. Return the
  image with detected-person boxes and access to the original. The teacher
  compares them and decides which situations need a closer look.
- Invalid input: an unsupported file or a JPEG that cannot be decoded.
  Return a clear reason and no detection result for that file. The teacher
  can replace it with a readable JPEG and try again.
- Valid input with an uncertain result: students are partly hidden or hard
  to see, or no people are detected. Keep the original available and allow
  the teacher to mark the result for manual review. A no-detection result
  must request review rather than report that no students are present.
  Missed people may remain even when some boxes are returned; the teacher
  checks the whole image before using the result.

### One quality that matters

- Usability: the teacher must be able to compare the original image with
  its detection result and see whether manual review is requested. We will
  check this in a walkthrough with an instructor using normal and uncertain
  examples. This walkthrough has not been done yet.

### One acceptance check

- Important failure: a partly hidden student is missed, so the teacher
  may overlook that student when reviewing the image.
- Metric that would show this failure: annotated-person recall at IoU >= 0.5,
  using the Lab 02 one-to-one matching method. Lower recall means more
  annotated people were missed. Review partly hidden students separately;
  the saved overall recall does not give a result for this group.
- Preliminary acceptance threshold: not set yet.
- Where will we check it? Use the fixed sample in
  [data/evaluation_manifest.json](../data/evaluation_manifest.json) for
  comparison with Lab 02, without tuning on it. A later acceptance evaluation
  needs more labelled classroom images, including partly hidden students,
  from videos separate from any future training or tuning data. Keep all
  frames from one video together, as in [the split strategy](split_strategy.md).
- Why this number for now? No acceptance number is supported yet. The measured
  0.710843 is a baseline result, not an acceptance threshold. We need the
  instructor's judgement of tolerable misses and better annotation coverage
  before choosing a limit. Prediction confidence 0.25 filters individual
  detections; it is not an acceptance threshold.
- Evidence still missing: instructor review of missed students; checked,
  more complete person annotations; labels identifying partly hidden students;
  and more independent classroom images with known video groups. We also
  need the teammate reproduction check described in the README.

### Failure cases

| Area | What could go wrong and why it matters | How would we notice it? | Planned response |
| --- | --- | --- | --- |
| Data or input | Corrupt JPEG cannot be read; no usable image to review | JPEG decoding fails | Explain the error; ask for a replacement image |
| Model behavior | Partly hidden student is missed; teacher may overlook them | Unmatched person annotation at IoU 0.5; low recall on reviewed occluded cases | Compare original and boxes; mark for manual review; count the miss in evaluation |
| Integration or workflow | Teacher reads person boxes as engagement labels; unsupported conclusions | Instructor walkthrough reveals this interpretation | Label outputs as person detections; explain the need for teacher review |
