FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_FROZEN=1 \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY pyproject.toml uv.lock ./
RUN uv sync --no-dev

COPY gateway/ gateway/
COPY postgres/ postgres/
COPY scripts/ scripts/

RUN useradd --create-home --uid 10001 aurum && chown -R aurum:aurum /app
USER aurum

EXPOSE 8000

CMD ["scripts/start-gateway.sh"]
