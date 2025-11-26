from pathlib import Path
from typing import Optional, Tuple, Any, Dict
import json

from fastapi import FastAPI, HTTPException, Body
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import joblib
import numpy as np


app = FastAPI(title="Life Expectancy Predictor", version="1.0")

# Allow CORS for all origins.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Load model info and artifacts at startup and check common locations.
MODELS_DIR = Path("models")
MODEL_INFO_PATH = Path("model_selection_info.json")
ALT_BASE = Path("linear_regression")


def _load_artifacts():
    # locate model_selection_info.json in likely locations
    info_path_candidates = [MODEL_INFO_PATH, ALT_BASE / "model_selection_info.json",
                            Path("linear_regression/model_selection_info.json")]
    info_path = next((p for p in info_path_candidates if p.exists()), None)
    if info_path is None:
        raise RuntimeError(
            f"Missing model_selection_info.json in any of: {info_path_candidates}")
    info = json.loads(info_path.read_text())
    features = info.get("features", [])
    best_name = info.get("best_model_by_rmse")
    # Determine model filename from info or common defaults
    candidate = info.get("best_model_path") or {
        "RandomForest": "random_forest.joblib",
        "LinearRegression": "linear_regression.joblib",
        "DecisionTree": "decision_tree_best.joblib",
    }.get(best_name, "random_forest.joblib")

    # Search for the model file in several likely locations
    model_path_candidates = [MODELS_DIR / candidate, ALT_BASE / "models" / candidate,
                             Path("models") / candidate, Path("linear_regression") / "models" / candidate]
    model_path = next((p for p in model_path_candidates if p.exists()), None)
    if model_path is None:
        raise RuntimeError(
            f"Model file not found in any of: {model_path_candidates}")

    model = joblib.load(model_path)

    # load scaler if available in common locations
    scaler = None
    scaler_candidates = [
        MODELS_DIR / "selected_scaler.joblib",
        ALT_BASE / "models" / "selected_scaler.joblib",
        ALT_BASE / "preprocessing_scaler.joblib",
        Path("selected_scaler.joblib"),
        Path("linear_regression") / "selected_scaler.joblib",
    ]
    scaler_path = next((p for p in scaler_candidates if p.exists()), None)
    if scaler_path is not None:
        scaler = joblib.load(scaler_path)

    return info, features, model, scaler


# Lazy cache for artifacts so the app starts quickly on Cloud Run.
_ARTIFACTS: Dict[str, Any] = {}


def get_artifacts() -> Tuple[Dict[str, Any], list, Any, Any]:
    """Return (info, features, model, scaler) and cache them on first access."""
    if _ARTIFACTS.get("loaded"):
        return _ARTIFACTS["info"], _ARTIFACTS["features"], _ARTIFACTS["model"], _ARTIFACTS["scaler"]
    info, features, model, scaler = _load_artifacts()
    _ARTIFACTS.update({"loaded": True, "info": info,
                      "features": features, "model": model, "scaler": scaler})
    return info, features, model, scaler


def _feature_ranges(name: str):
    """Return heuristic ranges for a feature (currently unused)."""
    return None, None


# Dynamically build a Pydantic model class for the features
def _build_input_model(features_list):
    # kept for compatibility if later desired; not used at import time
    namespace = {"__annotations__": {}}
    for f in features_list:
        namespace["__annotations__"][f] = Optional[float]
        namespace[f] = Field(None, description=f)
    namespace["__module__"] = __name__
    namespace["model_config"] = {"extra": "allow"}
    return type("FeaturesInput", (BaseModel,), namespace)


@app.post("/predict")
def predict(payload: dict = Body(..., description="Feature name -> numeric value map")):
    """Predict life expectancy from a feature name -> numeric value mapping."""
    info, FEATURES, MODEL, SCALER = get_artifacts()
    data = payload
    # Validate incoming payload values for the features used by the model:
    # Only validate features present in FEATURES and ignore extra metadata.
    for k in FEATURES:
        if k not in data:
            continue
        v = data[k]
        if v is None:
            continue
        if isinstance(v, (int, float)):
            continue
        try:
            float(v)
        except (ValueError, TypeError):
            raise HTTPException(
                status_code=422, detail=f"Invalid value for feature '{k}': {v}")
    # Ensure features are ordered for the model
    x = [data.get(f, 0.0) for f in FEATURES]
    arr = np.array(x).reshape(1, -1)
    if SCALER is not None:
        try:
            n_in = getattr(SCALER, "n_features_in_", None)
            if n_in is None or n_in == arr.shape[1]:
                arr = SCALER.transform(arr)
        except Exception:
            pass
    try:
        pred = MODEL.predict(arr)
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Model prediction failed: {e}")

    return {"prediction": float(pred[0]), "model": info.get("best_model_by_rmse", "unknown")}


# Also expose `/api/predict` so Hosting rewrites with `/api` work.
@app.post("/api/predict")
def predict_api(payload: dict = Body(..., description="Feature name -> numeric value map")):
    return predict(payload)


@app.get("/")
def root():
    return {"status": "ok", "docs": "/docs"}


# Expose OpenAPI and docs under `/api` to support Hosting rewrites.
@app.get("/api/openapi.json", include_in_schema=False)
def api_openapi():
    return app.openapi()


@app.get("/api/docs", include_in_schema=False)
def api_docs():
    return get_swagger_ui_html(openapi_url="/api/openapi.json", title="API Docs")


# Expose OpenAPI and docs at root paths as well.
@app.get("/openapi.json", include_in_schema=False)
def openapi_root():
    return app.openapi()


@app.get("/docs", include_in_schema=False)
def docs_root():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Life Expectancy Predictor - Swagger UI")


# Custom OpenAPI generator to inject a realistic example for /predict.
def _read_features_from_info():
    # Read the feature list from model_selection_info.json if present.
    info_path_candidates = [MODEL_INFO_PATH, ALT_BASE / "model_selection_info.json",
                            Path("linear_regression/model_selection_info.json")]
    info_path = next((p for p in info_path_candidates if p.exists()), None)
    if info_path is None:
        return []
    try:
        info = json.loads(info_path.read_text())
        return info.get("features", [])
    except Exception:
        return []


def custom_openapi():
    if getattr(app, "_custom_openapi", None):
        return app._custom_openapi
    from fastapi.openapi.utils import get_openapi

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        routes=app.routes,
    )

    # Build an example payload from model features using hosted examples if available.
    features = _read_features_from_info()

    def _example_from_examples(features_list):
        examples_dir = Path(__file__).resolve().parent / "examples"
        if not examples_dir.exists():
            return None
        # collect numeric values per feature from example files
        vals = {f: [] for f in features_list}
        for p in examples_dir.glob("*.json"):
            try:
                j = json.loads(p.read_text())
            except Exception:
                continue
            for f in features_list:
                if f not in j:
                    continue
                v = j[f]
                # accept numeric types or strings convertible to float
                if isinstance(v, (int, float)):
                    vals[f].append(float(v))
                else:
                    try:
                        vals[f].append(float(v))
                    except Exception:
                        # ignore non-numeric example values
                        continue
        # compute median per feature where possible
        example = {}
        for f in features_list:
            col = vals.get(f, [])
            if col:
                try:
                    example[f] = float(np.median(np.array(col)))
                except Exception:
                    example[f] = 0.0
            else:
                example[f] = 0.0
        return example

    example_payload = None
    if features:
        example_payload = _example_from_examples(features)
        if example_payload is None:
            example_payload = {f: 0.0 for f in features}
    else:
        example_payload = {"feature1": 0.0}

    # Inject the example into both /predict and /api/predict when present.
    for path_key in ("/predict", "/api/predict"):
        path_obj = openapi_schema.get("paths", {}).get(path_key)
        if not path_obj:
            continue
        post_op = path_obj.get("post")
        if not post_op:
            continue
        # Ensure requestBody exists in schema
        rb = post_op.setdefault("requestBody", {
            "content": {"application/json": {"schema": {"type": "object"}}}
        })
        content = rb.setdefault("content", {})
        app_json = content.setdefault("application/json", {})
        # Provide an example for the request body
        app_json.setdefault("example", example_payload)

    app._custom_openapi = openapi_schema
    return app._custom_openapi


app.openapi = custom_openapi
