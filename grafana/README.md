# Grafana Provisioning

Grafana is provisioned from files, not from the UI. The datasource and the dashboard loader are
defined under `grafana/provisioning/`, and dashboard JSON lives in `grafana/dashboards/`.

Provisioned objects are marked non-editable, so the repository stays the source of truth and UI
edits cannot drift away from it.

## Datasource

`provisioning/datasources/postgres.yaml` defines a single Postgres datasource with the fixed UID
`aurum-postgres`. Dashboards reference that UID rather than the datasource name, so renaming the
datasource never breaks a dashboard.

Every connection setting is read from the environment, so the same file works locally and in
production without edits.

| Variable | Default in Compose | Purpose |
| --- | --- | --- |
| `POSTGRES_HOST` | `postgres` | Database host |
| `POSTGRES_PORT` | `5432` | Database port |
| `POSTGRES_DB` | `mt5fx` | Database name |
| `POSTGRES_USER` | `mt5fx` | Database user |
| `POSTGRES_PASSWORD` | `change-me` | Database password, stored as a Grafana secret |
| `POSTGRES_SSLMODE` | `disable` | `disable` locally; use `require` or stricter in production |

Grafana does not support shell-style defaults such as `${VAR:-value}` in provisioning files. Every
variable above must be present in Grafana's environment, otherwise it interpolates to an empty
string. Compose supplies them all; other deployment targets must do the same.

An empty value fails in a way that does not name the missing variable. Omitting
`POSTGRES_SSLMODE` leaves `sslmode` empty, the driver then falls back to requiring TLS, and the
datasource reports:

```
pq: SSL is not enabled on the server
```

That message describes the server, so the cause looks like a Postgres misconfiguration rather than
an absent environment variable in Grafana.

The password is passed through `secureJsonData`, so Grafana stores it encrypted and never returns
it through the API.

The datasource is declared as `type: postgres`. Grafana 11 reports it back as
`grafana-postgresql-datasource`, which is the same plugin under its current name.

## Dashboards

`provisioning/dashboards/dashboards.yaml` points a file provider at `/var/lib/grafana/dashboards`,
which Compose mounts read-only from `grafana/dashboards/`. Any JSON file placed there is loaded
into the `Aurum` folder automatically, and the provider rescans every 10 seconds, so a new file
appears without restarting Grafana.

## Local Use

```bash
docker compose -f compose.dev.yaml --env-file .env up postgres migrate grafana
```

Grafana listens on `http://localhost:3000`. Check the datasource without opening the UI:

```bash
curl -su "$GRAFANA_ADMIN_USER:$GRAFANA_ADMIN_PASSWORD" \
  http://localhost:3000/api/datasources/uid/aurum-postgres/health
```

A healthy datasource answers `{"message":"Database Connection OK","status":"OK"}`.
