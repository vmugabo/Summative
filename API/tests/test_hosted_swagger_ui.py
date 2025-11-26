import requests
import pytest


HOSTED_BASE = "https://ml-summative.web.app/api"


def test_hosted_openapi_json_contains_predict():
    """Fetch the hosted OpenAPI JSON and assert the /predict path exists."""
    url = f"{HOSTED_BASE}/openapi.json"
    r = requests.get(url, timeout=10)
    assert r.status_code == 200, f"OpenAPI not reachable: {r.status_code}"
    j = r.json()
    assert isinstance(j, dict), "OpenAPI response is not JSON"
    paths = j.get("paths", {})
    assert "/predict" in paths or "/api/predict" in paths, "Predict path not found in OpenAPI"


def test_hosted_swagger_ui_reachable():
    """Ensure the hosted Swagger UI HTML is reachable at /api/docs."""
    url = f"{HOSTED_BASE}/docs"
    r = requests.get(url, timeout=10)
    assert r.status_code == 200, f"Swagger UI not reachable: {r.status_code}"
    ctype = r.headers.get("Content-Type", "")
    assert "text/html" in ctype, f"Expected HTML response for docs, got {ctype}"
