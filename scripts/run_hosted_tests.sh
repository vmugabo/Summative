#!/usr/bin/env bash
set -euo pipefail

# Run API smoke tests against the Firebase-hosted site and optionally open docs.
# Usage: ./scripts/run_hosted_tests.sh [--open-docs]

BASE_HOSTED="https://ml-summative.web.app"

echo "Running hosted API tests against $BASE_HOSTED"

# Run hosted tests (fetch example JSON from hosting and POST to the hosted API).
pytest -q API/tests/test_hosted_api_examples.py API/tests/test_hosted_swagger_ui.py || true

if [[ ${1-} == "--open-docs" ]]; then
  echo "Opening Swagger UI in Chrome..."
  open -a "Google Chrome" "$BASE_HOSTED/api/docs" || true
fi

echo "Done."
