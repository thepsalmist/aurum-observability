"""Create backtest analytics tables.

Revision ID: 20260721_002
Revises: 20260718_001
Create Date: 2026-07-21
"""

from __future__ import annotations

from pathlib import Path

from alembic import op

revision = "20260721_002"
down_revision = "20260718_001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    sql = Path(__file__).parents[1] / "002_backtest_analytics.sql"
    op.execute(sql.read_text().rstrip().removesuffix(";"))


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS backtest_blocked_entry_metrics CASCADE")
    op.execute("DROP TABLE IF EXISTS backtest_direction_metrics CASCADE")
    op.execute("DROP TABLE IF EXISTS backtest_close_reason_metrics CASCADE")
    op.execute("DROP TABLE IF EXISTS backtest_weekly_metrics CASCADE")
    op.execute("DROP TABLE IF EXISTS backtest_summary_metrics CASCADE")
    op.execute("DROP TABLE IF EXISTS backtest_artifacts CASCADE")
    op.execute("DROP TABLE IF EXISTS backtest_runs CASCADE")
