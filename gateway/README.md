# Artifact Gateway

FastAPI service that provides authenticated read-only access to backtest artifacts held in
private SeaweedFS/S3 storage. Grafana links to artifacts through this gateway so the storage
bucket itself can stay private.

## Configuration

All settings are read from the environment. There are no hardcoded defaults for credentials.

| Variable | Required | Default | Purpose |
| --- | --- | --- | --- |
| `SEAWEEDFS_S3_ENDPOINT_URL` | yes | — | S3-compatible endpoint for artifact storage |
| `SEAWEEDFS_S3_ACCESS_KEY` | yes | — | S3 access key |
| `SEAWEEDFS_S3_SECRET_KEY` | yes | — | S3 secret key |
| `SEAWEEDFS_BUCKET` | yes | — | Bucket holding backtest artifacts |
| `SEAWEEDFS_S3_REGION` | no | `us-east-1` | S3 region |
| `ARTIFACT_GATEWAY_AUTH_REQUIRED` | no | `true` | Whether requests must present a token |
| `ARTIFACT_GATEWAY_AUTH_TOKEN` | no | — | Token accepted by the gateway |

Configuration is validated at application startup, so a misconfigured gateway fails fast
instead of serving traffic.

The start script reads two further variables: `ARTIFACT_GATEWAY_HOST` (default `0.0.0.0`) and
`ARTIFACT_GATEWAY_PORT` (default `$PORT`, then `8000`).

## Running

`scripts/start-gateway.sh` is the single entrypoint, shared by the Compose stack and any other
deployment target.

As part of the Compose stack:

```bash
docker compose -f compose.dev.yaml --env-file .env up gateway
```

Directly, for iterating locally:

```bash
scripts/start-gateway.sh
```

With autoreload during development:

```bash
uv run uvicorn gateway.main:app --reload
```

Check that the service is up:

```bash
curl http://localhost:8000/healthz
```

## Authentication

Artifact requests require a bearer token, supplied as `Authorization: Bearer <token>` and checked
against `ARTIFACT_GATEWAY_AUTH_TOKEN`. Requests with a missing, malformed, or incorrect token get
`401` with a `WWW-Authenticate: Bearer` header. The comparison is constant-time, and the expected
token is never echoed in a response. Callers send:

```
Authorization: Bearer <token>
```

Authentication is on by default. Setting `ARTIFACT_GATEWAY_AUTH_REQUIRED=false` disables it, which
is intended only for local development against throwaway data.

When authentication is required, a non-blank `ARTIFACT_GATEWAY_AUTH_TOKEN` must be configured. The
service refuses to start otherwise, so it cannot come up unprotected by accident.

`/healthz` is deliberately unauthenticated so liveness probes work without credentials.

## Endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/healthz` | no | Liveness probe; returns `{"status": "ok"}` |
