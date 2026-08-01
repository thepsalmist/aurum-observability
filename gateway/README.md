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
| `ARTIFACT_GATEWAY_ALLOWED_FILENAMES` | no | see below | Comma-separated artifact filenames the gateway may serve |

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

## Request Validation

Profiles, run IDs, and filenames are validated before any storage access, so a rejected request
never reaches the object store. Authentication is checked first, so an unauthenticated caller
learns nothing about what the gateway will accept.

A profile or run ID must be a single path segment: it starts with a letter or digit, contains only
letters, digits, `.`, `-`, and `_`, never contains `..`, and is at most 128 characters. Anything
else is rejected with `400`.

Filenames are not pattern-matched, they are checked for exact membership in
`ARTIFACT_GATEWAY_ALLOWED_FILENAMES`. Traversal through the filename is therefore impossible by
construction. The default allowlist is:

```
report.html, summary.json, metrics.json, trades.csv, equity_curve.png, drawdown.png
```

Allowlist entries are themselves validated at startup with the same single-segment rule, so a
misconfigured entry such as `../escape.json` stops the service from starting rather than widening
what it will serve. The list must not be empty.

Status codes are split so they stay meaningful: `400` means the request itself was invalid, `404`
means the request was well-formed but no such object exists, and `502` means the object store
could not be reached or answered with a fault. A missing bucket is reported as `502` rather than
`404`, so a deployment mistake is never mistaken for an absent artifact. Error messages are fixed
strings and never echo the submitted value.

## Storage Layout

Artifacts are read from the bucket in `SEAWEEDFS_BUCKET` using the key layout the backtest
publisher writes:

```
runs/{profile}/{run_id}/{filename}
```

A profile is a trading profile such as `gold` or `jpy`, defined by the corresponding `.toml` in
the backtest project. The request path maps onto the key one segment at a time, and every segment
is validated first, so the key is always built from known-safe values.

```
GET /artifacts/runs/jpy_benchmark/100cd43sed/report.html
 -> runs/jpy_benchmark/100cd43sed/report.html
```

Responses stream the object body rather than buffering it, and carry the stored `Content-Length`,
`ETag`, and `Last-Modified`. The content type is whatever storage recorded, falling back to a type
guessed from the filename when the publisher left it as `binary/octet-stream`. Every response
carries `X-Content-Type-Options: nosniff`.

## Endpoints

| Method | Path | Auth | Description |
| --- | --- | --- | --- |
| `GET` | `/healthz` | no | Liveness probe; returns `{"status": "ok"}` |
| `GET` | `/artifacts/runs/{profile}/{run_id}/{filename}` | yes | Streams one allowlisted artifact |
