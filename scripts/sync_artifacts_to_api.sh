#!/usr/bin/env bash
set -euo pipefail

# Copy `linear_regression/` artifacts into `API/linear_regression/` so they are included when deploying with `--source API`.

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/linear_regression"
DEST_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/API/linear_regression"

echo "Source: $SRC_DIR"
echo "Destination: $DEST_DIR"

if [ ! -d "$SRC_DIR" ]; then
  echo "Error: source directory does not exist: $SRC_DIR" >&2
  exit 2
fi

rm -rf "$DEST_DIR"
mkdir -p "$DEST_DIR"

echo "Copying files..."
cp -a "$SRC_DIR/." "$DEST_DIR/"

echo "Listing copied files:"
ls -al "$DEST_DIR" | sed -n '1,200p'

echo "Done. Now you can deploy with: gcloud run deploy api-service --source API --region us-central1 --platform managed --project ml-summative"
