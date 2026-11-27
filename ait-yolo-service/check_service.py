"""Send the two Lab 07 requests from another computer and save their responses."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from uuid import uuid4


def read_json(request: Request, timeout: float) -> dict[str, Any]:
    try:
        response = urlopen(request, timeout=timeout)
    except HTTPError as error:
        response = error
    with response:
        return {"http_status": response.code, "body": json.load(response)}


def upload(
    base_url: str,
    request_id: str,
    data: bytes,
    filename: str,
    content_type: str,
    timeout: float,
) -> dict[str, Any]:
    boundary = f"lab07-{uuid4().hex}"
    body = (
        f"--{boundary}\r\n"
        'Content-Disposition: form-data; name="request_id"\r\n\r\n'
        f"{request_id}\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8") + data + f"\r\n--{boundary}--\r\n".encode("ascii")
    return read_json(
        Request(
            f"{base_url}/predict",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        ),
        timeout,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--image", required=True, type=Path)
    parser.add_argument("--request-prefix", default=f"lab07-{uuid4().hex[:8]}")
    parser.add_argument("--timeout", type=float, default=300)
    parser.add_argument(
        "--output", type=Path, default=Path("reports/lab07_client_check.json")
    )
    args = parser.parse_args()

    try:
        suffix = args.image.suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png"}:
            raise ValueError("Use a JPEG or PNG example.")
        data = args.image.read_bytes()
        base_url = args.base_url.rstrip("/")
        health = read_json(Request(f"{base_url}/health"), args.timeout)
        valid_id = f"{args.request_prefix}-valid"
        invalid_id = f"{args.request_prefix}-invalid"
        valid = upload(
            base_url,
            valid_id,
            data,
            f"example{suffix}",
            "image/png" if suffix == ".png" else "image/jpeg",
            args.timeout,
        )
        invalid = upload(
            base_url, invalid_id, b"This is not an image.\n",
            "notes.txt", "text/plain", args.timeout,
        )
        valid_body = valid["body"]
        invalid_body = invalid["body"]
        checks = {
            "health": health["http_status"] == 200
            and health["body"].get("status") == "ok",
            "valid_prediction": valid["http_status"] == 200
            and valid_body.get("request_id") == valid_id
            and valid_body.get("status") == "pass"
            and valid_body.get("action") == "continue_to_prediction"
            and valid_body.get("prediction_called") is True
            and isinstance(valid_body.get("prediction"), dict),
            "invalid_rejected": invalid["http_status"] == 400
            and invalid_body.get("request_id") == invalid_id
            and invalid_body.get("status") == "error"
            and invalid_body.get("action") == "reject_input"
            and invalid_body.get("prediction_called") is False
            and invalid_body.get("prediction") is None,
        }
        report = {
            "base_url": base_url,
            "image": args.image.name,
            "checks": checks,
            "health": health,
            "valid": valid,
            "invalid": invalid,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        for name, passed in checks.items():
            print(f"{name}: {'PASS' if passed else 'FAIL'}")
        print(f"Request IDs: {valid_id}, {invalid_id}")
        print(f"Responses saved to: {args.output}")
        return 0 if all(checks.values()) else 1
    except (OSError, ValueError) as error:
        print(f"Service check failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
