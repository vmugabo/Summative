import os
import subprocess
import requests
import pytest


def resolve_cloudrun_url():
    # Use CLOUDRUN_URL env override if provided.
    env = os.getenv("CLOUDRUN_URL")
    if env:
        return env.rstrip('/')

    # Query gcloud for the first service URL in us-central1 if available.
    try:
        out = subprocess.check_output([
            "gcloud",
            "run",
            "services",
            "list",
            "--platform",
            "managed",
            "--region",
            "us-central1",
            "--format=value(status.url)"
        ], stderr=subprocess.DEVNULL)
        url = out.decode().strip().splitlines()
        if url:
            return url[0].rstrip('/')
    except Exception:
        pass

    pytest.skip(
        "Could not determine Cloud Run service URL; set CLOUDRUN_URL or configure gcloud")


BASE = resolve_cloudrun_url()
PREDICT = f"{BASE}/predict"

EXAMPLE_PATHS = [
    ("examples/example_valid1.json", 200),
    ("examples/example_valid2.json", 200),
    ("examples/example_edge.json", 200),
    ("examples/example_invalid.json", 422),
]


@pytest.mark.parametrize("path,expected", EXAMPLE_PATHS)
def test_cloudrun_examples(path, expected):
    # Fetch example JSON from hosting (examples are published at the hosted web root).
    hosted_base = "https://ml-summative.web.app"
    example_url = f"{hosted_base}/{path}"
    r = requests.get(example_url, timeout=10)
    assert r.status_code == 200, f"Failed to fetch example {path} from hosting"
    payload = r.json()

    resp = requests.post(PREDICT, json=payload, timeout=20)
    if resp.status_code != expected:
        body = None
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        pytest.fail(
            f"{path} -> expected {expected}, got {resp.status_code}: {body}")
