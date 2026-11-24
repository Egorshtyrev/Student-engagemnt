# Lab 07: containerised inference service

## Service and container boundary

This packages the existing Lab 06 API in `ait-yolo-service/`. Its routes stay
`GET /health`, `GET /docs` and `POST /predict`. The API checks the uploaded
JPEG or PNG before prediction and appends each decision to JSONL.

The Docker image contains Python 3.12, the pinned service dependencies,
API files, input contract, tests and the request-check script. The build
context is `ait-yolo-service/`, so the repository's dataset and Lab 02 weights
are outside it. `.dockerignore` also excludes environments, credentials,
weights and generated reports. `.env` and evidence are supplied at runtime.

The Lab 06 settings use pretrained `yolo26n.pt` on CPU, confidence 0.25 and
image size 640. The first valid request downloads the weights. This is the
cloud API demonstration; it does not reproduce the Lab 02 YOLOv8m recall
experiment or measure student engagement. A teacher still reviews results.

## Build and run on the Ubuntu VM

Connect with the team's SSH key, then open the repository's service folder:

```bash
cd ~/Student-engagemnt/ait-yolo-service
docker --version
docker buildx version
df -h /
```

Use the actual repository location if it differs. If Docker or Buildx is
missing, install the packages from the course instructions:

```bash
sudo apt update
sudo apt install -y docker.io docker-buildx
sudo systemctl enable --now docker
sudo docker run --rm hello-world
```

Prepare the configuration without overwriting an existing `.env`:

```bash
test -f .env || cp .env.example .env
mkdir -p reports
sudo docker build -t student-engagement-service:1 .
sudo docker run --rm student-engagement-service:1 python -m unittest discover -s tests -v
```

Continue when the tests report `OK`. They use a fake predictor, so they
check input routing and JSONL writing without downloading model weights.
The replacement test checks that a new application instance preserves and
appends to an existing journal. The container check below tests the mount.

```bash
sudo docker run -d --rm --name student-engagement-service \
  -p 8000:8000 \
  --env-file .env \
  --mount type=bind,src="$(pwd)/reports",dst=/app/reports \
  student-engagement-service:1
sudo docker logs student-engagement-service
```

Wait for `Application startup complete`. `EVIDENCE_PATH` in `.env` must
remain `reports/yolo_predictions.jsonl` so the journal is inside the mount.
`model_loaded: false` before the first valid request is expected.

## Two requests from another computer

Open `http://<public-ip>:8000/health` and
`http://<public-ip>:8000/docs` on your own computer. Replace `<public-ip>`
with the current VM address.

From the repository root on that computer, use the same classroom example
as the earlier inference demo. The script needs only Python's standard library:

```powershell
py ait-yolo-service/check_service.py --base-url http://<public-ip>:8000 --image dataset/images/1-second-scene_mp4-0000_jpg.rf.FEE3uKUksPQqBY0UDCWZ.jpg --request-prefix lab07 --output ait-yolo-service/reports/lab07_client_check.json
```

On macOS/Linux use `python3` instead of `py`. Allow several minutes for the
first model download and CPU prediction. The script checks `/health`, sends
the classroom JPEG as `lab07-valid`, then sends a text file as `lab07-invalid`.
It prints three `PASS` results and saves the full responses locally. A failed
check returns a nonzero exit code. Use a different prefix for a later run.

In `/docs`, the same requests can be sent manually through **POST /predict**:

| Input | Expected HTTP status | Action | Prediction called |
| --- | --- | --- | --- |
| Classroom JPEG | 200 | `continue_to_prediction` | `true` |
| Text file | 400 | `reject_input` | `false` |

HTTP 400 is the expected rejection. The response includes the failed checks
and `prediction: null`. HTTP 503 means inference was attempted but failed;
it is not a successful valid-input demonstration.

## Check evidence and replace the container

On the VM, still in `ait-yolo-service/`, inspect both records and save a
checksum before replacing the container. Run this after the two requests
finish and before sending any more predictions:

```bash
sudo tail -n 2 reports/yolo_predictions.jsonl
sudo sha256sum reports/yolo_predictions.jsonl > reports/lab07_evidence.sha256
sudo docker inspect --format '{{.Id}}' student-engagement-service > reports/lab07_container_before.txt
sudo docker stop student-engagement-service
sudo docker run -d --rm --name student-engagement-service \
  -p 8000:8000 \
  --env-file .env \
  --mount type=bind,src="$(pwd)/reports",dst=/app/reports \
  student-engagement-service:1
sudo docker logs student-engagement-service
sudo docker inspect --format '{{.Id}}' student-engagement-service > reports/lab07_container_after.txt
```

Wait for startup and open `/health` again **from the other computer**.
Do this before another `/predict`, because a prediction appends evidence.
Back on the VM, check that the container ID changed and the journal did not:

```bash
if cmp -s reports/lab07_container_before.txt reports/lab07_container_after.txt; then
  echo 'FAIL: container was not replaced'
else
  echo 'PASS: new container ID'
fi
sudo sha256sum -c reports/lab07_evidence.sha256
sudo tail -n 2 reports/yolo_predictions.jsonl
```

The checksum must report `OK`, and the two request IDs must still be present.
The new container can show `model_loaded: false`: the model is lazy-loaded
and its in-memory state is separate from the journal on the VM. Weights are
not mounted in this example, so the next valid request may download them again.

## If Docker does not work

Check the current state before changing anything:

```bash
sudo docker ps -a
sudo docker logs student-engagement-service
sudo docker system df
df -h /
sudo ss -ltnp 'sport = :8000'
```

If port 8000 is occupied, identify the earlier Lab 06 Uvicorn process or
container and stop that service before starting this one. If the name is
occupied, inspect the existing container and stop it before reusing the name.
Use `sudo docker` if the account cannot access the Docker socket. If disk
space is low, inspect usage before deciding what can be removed.

For a failed prediction, check the container logs and VM internet access.
For an unreachable API, check the current public IP, port mapping and VM
firewall/security-group rule for TCP 8000. For missing evidence, inspect
the bind mount and `EVIDENCE_PATH`; do not write it outside `/app/reports`.

## Defense and completion

Keep the client response file, the two container IDs, checksum result and
terminal screenshots for the defense. Generated output stays outside Git.
Another teammate should repeat the build and requests from these commands.
Agree who explains the input checks, model output and evidence persistence.

Completion requires the real container build and tests, successful requests
from another computer, and preserved evidence after replacement. Unit tests
alone do not prove cloud access or Docker persistence.

Local checks on 25 November 2026 used Windows and Python 3.12: all five API
tests and three Lab 05 tests passed, and `pip check` found no conflicts.
The classroom JPEG reached real `yolo26n.pt` inference (HTTP 200); a text file
was rejected before prediction (HTTP 400). After replacing the local Uvicorn
process, `/health` answered and the two-record journal had the same SHA-256.
Responses and restart output are saved locally in `ait-yolo-service/reports/`.
Docker build, tests inside the image, VM requests and container replacement
are still unverified: this computer has no Docker runtime and the VM SSH key
has not been provided. These remain necessary to complete the Lab.

When the demonstration is finished:

```bash
sudo docker stop student-engagement-service
```

Stop the VM through Yandex Cloud when the team is done; start it again
before the defense. The image and journal remain on the VM disk.

Requirements: [Lab 07 course instructions](https://github.com/naziherrahel/ai-implementation-technologies-students/tree/main/labs/lab_07).
