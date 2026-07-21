#!/bin/sh
set -eu

ALEMBIC_CONFIG="${ALEMBIC_CONFIG:-postgres/alembic.ini}"
ALEMBIC_TARGET="${ALEMBIC_TARGET:-head}"

uv run alembic -c "$ALEMBIC_CONFIG" upgrade "$ALEMBIC_TARGET"
