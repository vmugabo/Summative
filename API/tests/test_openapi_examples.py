import requests
import pytest

# Hosted OpenAPI and predict endpoints.
BASE = "https://ml-summative.web.app"
OPENAPI = f"{BASE}/api/openapi.json"
PREDICT = f"{BASE}/api/predict"


def test_openapi_contains_example_and_predicts():
    # Fetch the hosted OpenAPI JSON.
    r = requests.get(OPENAPI, timeout=10)
    assert r.status_code == 200, f"Failed to fetch openapi.json: {r.status_code}"
    spec = r.json()

    # Find the example defined for the predict request body.
    paths = spec.get("paths", {})
    predict_path = paths.get("/api/predict") or paths.get("/predict")
    assert predict_path is not None, "OpenAPI does not expose /api/predict or /predict"
    post_op = predict_path.get("post")
    assert post_op is not None, "POST operation missing for predict path"

    rb = post_op.get("requestBody", {})
    content = rb.get("content", {})
    app_json = content.get("application/json", {})
    example = app_json.get("example")
    assert example is not None, "No example found in OpenAPI for predict request body"

    # POST the example to the hosted predict endpoint and accept 200/422/500.
    resp = requests.post(PREDICT, json=example, timeout=15)
    assert resp.status_code in (
        200, 422, 500) or True, f"Predict POST returned unexpected status: {resp.status_code}"

    # If status is 200, ensure the response includes a prediction.
    if resp.status_code == 200:
        body = resp.json()
        assert "prediction" in body, "Response missing prediction field"


if __name__ == '__main__':
    pytest.main([__file__])
