FROM python:3.11-slim

# Use the API subdirectory as the working directory so module imports like
# `prediction` resolve cleanly and relative paths find `linear_regression/`.
WORKDIR /app/API

# Install required system packages.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching and note build context for `--source API`.
COPY requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy app files from the API build context.
# When building from the `API/` directory we include model artifacts copied into
# `API/models` and `API/model_selection_info.json`. Explicitly copy them so the
# image always contains the trained artifacts.
COPY . /app

# If model files were placed inside the build context (API/models and
# API/model_selection_info.json), copy them into the image at predictable
# locations. These COPY commands are no-ops if the sources are not present.
# Copy model artifacts into locations the app searches for. Place copies
# under both `/app` and `/app/API` so relative lookups succeed regardless
# of the working directory used at runtime.
COPY model_selection_info.json /app/model_selection_info.json
COPY model_selection_info.json /app/linear_regression/model_selection_info.json
COPY model_selection_info.json /app/API/linear_regression/model_selection_info.json

# Copy joblib model artifacts into predictable `linear_regression/models`
# folders so `_load_artifacts()` can find them using relative paths.
COPY models/ /app/models/
COPY models/ /app/linear_regression/models/
COPY models/ /app/API/linear_regression/models/

# Ensure Python can import both the application package and the model package
# when the container starts.
ENV PYTHONPATH=/app:/app/API

ENV PORT=8080

EXPOSE ${PORT}

CMD ["uvicorn", "prediction:app", "--host", "0.0.0.0", "--port", "8080"]
