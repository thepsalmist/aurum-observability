# Postgres Migrations

Postgres schema changes are managed with Alembic, but the schema source of truth is hand-written SQL. Alembic provides migration ordering, revision history, and the `alembic_version` table.

The initial baseline revision contains no schema changes. The first table-creating revisions define the live trading and backtest schemas.

## Configuration

Set `DATABASE_URL` when running migrations:

```bash
export DATABASE_URL=postgresql+psycopg://mt5fx:change-me@localhost:5432/mt5fx
```

The Alembic environment can also build the URL from `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_PORT`, and `POSTGRES_DB`.

## Commands

```bash
uv run alembic -c postgres/alembic.ini upgrade head
uv run alembic -c postgres/alembic.ini current
uv run alembic -c postgres/alembic.ini downgrade -1
```

## Adding A SQL Migration

1. Add the reviewed SQL file under `postgres/migrations/`.
2. Add an Alembic revision under `postgres/migrations/versions/`.
3. In the revision, execute the SQL file in `upgrade()`.
4. Keep `downgrade()` explicit and conservative.

Example revision pattern:

```python
from pathlib import Path

from alembic import op

revision = "20260718_001"
down_revision = "20260718_000"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = Path(__file__).parents[1] / "001_live_trading.sql"
    op.execute(sql.read_text().rstrip().removesuffix(";"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS bot_heartbeats CASCADE")
```

## Migration Inventory

- `20260718_000`: baseline revision with no schema changes.
- `20260718_001`: live trading observability tables.
