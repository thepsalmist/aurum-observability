#!/bin/sh
set -eu

ARTIFACT_GATEWAY_HOST="${ARTIFACT_GATEWAY_HOST:-0.0.0.0}"
ARTIFACT_GATEWAY_PORT="${ARTIFACT_GATEWAY_PORT:-${PORT:-8000}}"

exec uv run --no-dev uvicorn gateway.main:app \
  --host "$ARTIFACT_GATEWAY_HOST" \
  --port "$ARTIFACT_GATEWAY_PORT"
