import json
import requests
import pytest


BASE = "https://ml-summative.web.app"
PREDICT = f"{BASE}/api/predict"

EXAMPLES = {
    "example_valid1.json": {"path": "examples/example_valid1.json", "expect": 200},
    "example_valid2.json": {"path": "examples/example_valid2.json", "expect": 200},
    "example_edge.json": {"path": "examples/example_edge.json", "expect": 200},
    "example_invalid.json": {"path": "examples/example_invalid.json", "expect": 422},
}


@pytest.mark.parametrize("name,info", list(EXAMPLES.items()))
def test_hosted_example_against_hosted_api(name, info):
    example_url = f"{BASE}/{info['path']}"

    # Fetch example JSON from the hosted site.
    r = requests.get(example_url, timeout=10)
    assert r.status_code == 200, f"Failed to fetch example {name}: {r.status_code}"
    try:
        payload = r.json()
    except Exception as e:
        pytest.fail(f"Example {name} is not valid JSON: {e}")

    # Post the payload to the hosted API.
    headers = {"Content-Type": "application/json"}
    resp = requests.post(PREDICT, json=payload, headers=headers, timeout=15)

    # Show helpful debug output on failure.
    if resp.status_code != info["expect"]:
        try:
            body = resp.json()
        except Exception:
            body = resp.text
        pytest.fail(
            f"Example {name} -> expected {info['expect']}, got {resp.status_code}: {body}")
