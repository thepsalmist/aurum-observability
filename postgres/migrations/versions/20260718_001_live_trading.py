"""Create live trading observability tables.

Revision ID: 20260718_001
Revises: 20260718_000
Create Date: 2026-07-18
"""

from __future__ import annotations

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
    op.execute("DROP TABLE IF EXISTS daily_risk_snapshots CASCADE")
    op.execute("DROP TABLE IF EXISTS open_position_snapshots CASCADE")
    op.execute("DROP TABLE IF EXISTS trade_events CASCADE")
    op.execute("DROP TABLE IF EXISTS account_snapshots CASCADE")
    op.execute("DROP TABLE IF EXISTS bot_heartbeats CASCADE")
