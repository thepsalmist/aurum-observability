# Aurum Observability

Public observability stack for MT5 FX live trading telemetry, historical backtest analytics, Grafana dashboards, and private artifact access.

This repository owns the public infrastructure and dashboard contract. The private `mt5_fx` repository owns MetaTrader 5 integration, live bot execution, backtests, benchmarks, and data publishers.

## Repository Scope

`aurum-observability` provides the infrastructure, schemas, dashboards, and gateway application needed to operate the observability stack. Runtime configuration is supplied through environment variables.

## Planned Stack

- `uv` for Python tooling.
- Postgres as the Grafana query source of truth.
- SQL-first Alembic migrations for schema versioning.
- Grafana provisioning for dashboards and datasources.
- SeaweedFS using its S3-compatible API for private artifact storage.
- FastAPI artifact gateway for authenticated read-only artifact access.
- Docker Compose for local development only.
- Dokku for production deployment.

## Project Layout

The repository starts with the shared project metadata and documentation. Service-specific directories are added by the implementation issues that introduce real files for Postgres, Grafana, SeaweedFS, the artifact gateway, scripts, and deployment docs.

## Development

Install dependencies with `uv`:

```bash
uv sync
```

Copy the example environment for local development:

```bash
cp .env.example .env
```

Do not commit `.env` or any generated runtime artifacts.

## Implementation Status

This repository is being bootstrapped through GitHub issues before implementation PRs. Start with the foundation issues before adding dashboards or production deployment flows.
