# API example payloads

Example JSON payloads for testing the `/predict` endpoint.

Files:

- `example_valid1.json` — representative developing-country payload.
- `example_valid2.json` — representative developed-country payload.
- `example_edge.json` — extreme values payload.
- `example_invalid.json` — intentionally invalid payload for testing.

Quick hosted curl examples:

```bash
# valid (hosted)
curl -i -H "Content-Type: application/json" \
  -X POST https://ml-summative.web.app/api/predict \
  --data-binary @API/examples/example_valid1.json

# invalid (hosted)
curl -i -H "Content-Type: application/json" \
  -X POST https://ml-summative.web.app/api/predict \
  --data-binary @API/examples/example_invalid.json
```

Add more examples here for integration tests or CI.
