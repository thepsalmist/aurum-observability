CREATE TABLE backtest_runs (
    id BIGSERIAL PRIMARY KEY,
    run_id TEXT NOT NULL,
    run_group TEXT,
    strategy_name TEXT NOT NULL,
    strategy_version TEXT,
    variant_name TEXT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    period_start DATE NOT NULL,
    period_end DATE NOT NULL,
    status TEXT NOT NULL,
    initial_balance DOUBLE PRECISION,
    currency TEXT,
    parameters JSONB NOT NULL DEFAULT '{}'::jsonb,
    executed_at TIMESTAMPTZ NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT backtest_runs_run_id_key UNIQUE (run_id),
    CONSTRAINT backtest_runs_run_id_not_blank CHECK (btrim(run_id) <> ''),
    CONSTRAINT backtest_runs_run_group_not_blank CHECK (run_group IS NULL OR btrim(run_group) <> ''),
    CONSTRAINT backtest_runs_strategy_name_not_blank CHECK (btrim(strategy_name) <> ''),
    CONSTRAINT backtest_runs_strategy_version_not_blank CHECK (strategy_version IS NULL OR btrim(strategy_version) <> ''),
    CONSTRAINT backtest_runs_variant_name_not_blank CHECK (btrim(variant_name) <> ''),
    CONSTRAINT backtest_runs_symbol_not_blank CHECK (btrim(symbol) <> ''),
    CONSTRAINT backtest_runs_timeframe_not_blank CHECK (btrim(timeframe) <> ''),
    CONSTRAINT backtest_runs_status_not_blank CHECK (btrim(status) <> ''),
    CONSTRAINT backtest_runs_currency_not_blank CHECK (currency IS NULL OR btrim(currency) <> ''),
    CONSTRAINT backtest_runs_period_order CHECK (period_end >= period_start),
    CONSTRAINT backtest_runs_initial_balance_non_negative CHECK (initial_balance IS NULL OR initial_balance >= 0),
    CONSTRAINT backtest_runs_parameters_is_object CHECK (jsonb_typeof(parameters) = 'object')
);

CREATE INDEX backtest_runs_strategy_variant_executed_at_idx
    ON backtest_runs (strategy_name, variant_name, executed_at DESC);

CREATE INDEX backtest_runs_symbol_timeframe_executed_at_idx
    ON backtest_runs (symbol, timeframe, executed_at DESC);

CREATE INDEX backtest_runs_period_idx
    ON backtest_runs (period_start, period_end);

CREATE INDEX backtest_runs_run_group_executed_at_idx
    ON backtest_runs (run_group, executed_at DESC)
    WHERE run_group IS NOT NULL;

CREATE TABLE backtest_artifacts (
    id BIGSERIAL PRIMARY KEY,
    backtest_run_id BIGINT NOT NULL REFERENCES backtest_runs (id) ON DELETE CASCADE,
    artifact_type TEXT NOT NULL,
    object_key TEXT NOT NULL,
    content_type TEXT,
    byte_size BIGINT,
    sha256 TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT backtest_artifacts_run_type_key UNIQUE (backtest_run_id, artifact_type),
    CONSTRAINT backtest_artifacts_artifact_type_not_blank CHECK (btrim(artifact_type) <> ''),
    CONSTRAINT backtest_artifacts_object_key_not_blank CHECK (btrim(object_key) <> ''),
    CONSTRAINT backtest_artifacts_content_type_not_blank CHECK (content_type IS NULL OR btrim(content_type) <> ''),
    CONSTRAINT backtest_artifacts_object_key_is_not_url CHECK (
        object_key !~* '^[a-z][a-z0-9+.-]*://'
        AND position('?' in object_key) = 0
        AND position('#' in object_key) = 0
        AND left(object_key, 1) <> '/'
        AND object_key !~ '(^|/)\.\.(/|$)'
    ),
    CONSTRAINT backtest_artifacts_byte_size_non_negative CHECK (byte_size IS NULL OR byte_size >= 0),
    CONSTRAINT backtest_artifacts_sha256_format CHECK (sha256 IS NULL OR sha256 ~ '^[0-9a-f]{64}$')
);

CREATE INDEX backtest_artifacts_object_key_idx
    ON backtest_artifacts (object_key);

CREATE TABLE backtest_summary_metrics (
    id BIGSERIAL PRIMARY KEY,
    backtest_run_id BIGINT NOT NULL REFERENCES backtest_runs (id) ON DELETE CASCADE,
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    net_profit DOUBLE PRECISION,
    gross_profit DOUBLE PRECISION,
    gross_loss DOUBLE PRECISION,
    profit_factor DOUBLE PRECISION,
    expected_payoff DOUBLE PRECISION,
    max_drawdown DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    sharpe_ratio DOUBLE PRECISION,
    sortino_ratio DOUBLE PRECISION,
    recovery_factor DOUBLE PRECISION,
    win_rate_pct DOUBLE PRECISION,
    average_win DOUBLE PRECISION,
    average_loss DOUBLE PRECISION,
    largest_win DOUBLE PRECISION,
    largest_loss DOUBLE PRECISION,
    average_trade_duration_seconds DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT backtest_summary_metrics_run_key UNIQUE (backtest_run_id),
    CONSTRAINT backtest_summary_metrics_total_trades_non_negative CHECK (total_trades >= 0),
    CONSTRAINT backtest_summary_metrics_winning_trades_non_negative CHECK (winning_trades >= 0),
    CONSTRAINT backtest_summary_metrics_losing_trades_non_negative CHECK (losing_trades >= 0),
    CONSTRAINT backtest_summary_metrics_total_covers_results CHECK (total_trades >= winning_trades + losing_trades),
    CONSTRAINT backtest_summary_metrics_profit_factor_non_negative CHECK (profit_factor IS NULL OR profit_factor >= 0),
    CONSTRAINT backtest_summary_metrics_drawdown_non_negative CHECK (max_drawdown IS NULL OR max_drawdown >= 0),
    CONSTRAINT backtest_summary_metrics_drawdown_pct_range CHECK (max_drawdown_pct IS NULL OR (max_drawdown_pct >= 0 AND max_drawdown_pct <= 100)),
    CONSTRAINT backtest_summary_metrics_win_rate_pct_range CHECK (win_rate_pct IS NULL OR (win_rate_pct >= 0 AND win_rate_pct <= 100)),
    CONSTRAINT backtest_summary_metrics_average_duration_non_negative CHECK (
        average_trade_duration_seconds IS NULL OR average_trade_duration_seconds >= 0
    )
);

CREATE INDEX backtest_summary_metrics_net_profit_idx
    ON backtest_summary_metrics (net_profit DESC);

CREATE INDEX backtest_summary_metrics_drawdown_pct_idx
    ON backtest_summary_metrics (max_drawdown_pct ASC);

CREATE TABLE backtest_weekly_metrics (
    id BIGSERIAL PRIMARY KEY,
    backtest_run_id BIGINT NOT NULL REFERENCES backtest_runs (id) ON DELETE CASCADE,
    week_start DATE NOT NULL,
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    net_profit DOUBLE PRECISION,
    gross_profit DOUBLE PRECISION,
    gross_loss DOUBLE PRECISION,
    max_drawdown_pct DOUBLE PRECISION,
    win_rate_pct DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT backtest_weekly_metrics_run_week_key UNIQUE (backtest_run_id, week_start),
    CONSTRAINT backtest_weekly_metrics_total_trades_non_negative CHECK (total_trades >= 0),
    CONSTRAINT backtest_weekly_metrics_winning_trades_non_negative CHECK (winning_trades >= 0),
    CONSTRAINT backtest_weekly_metrics_losing_trades_non_negative CHECK (losing_trades >= 0),
    CONSTRAINT backtest_weekly_metrics_total_covers_results CHECK (total_trades >= winning_trades + losing_trades),
    CONSTRAINT backtest_weekly_metrics_drawdown_pct_range CHECK (max_drawdown_pct IS NULL OR (max_drawdown_pct >= 0 AND max_drawdown_pct <= 100)),
    CONSTRAINT backtest_weekly_metrics_win_rate_pct_range CHECK (win_rate_pct IS NULL OR (win_rate_pct >= 0 AND win_rate_pct <= 100))
);

CREATE INDEX backtest_weekly_metrics_week_start_idx
    ON backtest_weekly_metrics (week_start);

CREATE TABLE backtest_close_reason_metrics (
    id BIGSERIAL PRIMARY KEY,
    backtest_run_id BIGINT NOT NULL REFERENCES backtest_runs (id) ON DELETE CASCADE,
    close_reason TEXT NOT NULL,
    total_trades INTEGER NOT NULL,
    net_profit DOUBLE PRECISION,
    average_profit DOUBLE PRECISION,
    win_rate_pct DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT backtest_close_reason_metrics_run_reason_key UNIQUE (backtest_run_id, close_reason),
    CONSTRAINT backtest_close_reason_metrics_close_reason_not_blank CHECK (btrim(close_reason) <> ''),
    CONSTRAINT backtest_close_reason_metrics_total_trades_non_negative CHECK (total_trades >= 0),
    CONSTRAINT backtest_close_reason_metrics_win_rate_pct_range CHECK (win_rate_pct IS NULL OR (win_rate_pct >= 0 AND win_rate_pct <= 100))
);

CREATE INDEX backtest_close_reason_metrics_reason_idx
    ON backtest_close_reason_metrics (close_reason);

CREATE TABLE backtest_direction_metrics (
    id BIGSERIAL PRIMARY KEY,
    backtest_run_id BIGINT NOT NULL REFERENCES backtest_runs (id) ON DELETE CASCADE,
    direction TEXT NOT NULL,
    total_trades INTEGER NOT NULL,
    winning_trades INTEGER NOT NULL,
    losing_trades INTEGER NOT NULL,
    net_profit DOUBLE PRECISION,
    average_profit DOUBLE PRECISION,
    win_rate_pct DOUBLE PRECISION,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT backtest_direction_metrics_run_direction_key UNIQUE (backtest_run_id, direction),
    CONSTRAINT backtest_direction_metrics_direction_not_blank CHECK (btrim(direction) <> ''),
    CONSTRAINT backtest_direction_metrics_total_trades_non_negative CHECK (total_trades >= 0),
    CONSTRAINT backtest_direction_metrics_winning_trades_non_negative CHECK (winning_trades >= 0),
    CONSTRAINT backtest_direction_metrics_losing_trades_non_negative CHECK (losing_trades >= 0),
    CONSTRAINT backtest_direction_metrics_total_covers_results CHECK (total_trades >= winning_trades + losing_trades),
    CONSTRAINT backtest_direction_metrics_win_rate_pct_range CHECK (win_rate_pct IS NULL OR (win_rate_pct >= 0 AND win_rate_pct <= 100))
);

CREATE INDEX backtest_direction_metrics_direction_idx
    ON backtest_direction_metrics (direction);

CREATE TABLE backtest_blocked_entry_metrics (
    id BIGSERIAL PRIMARY KEY,
    backtest_run_id BIGINT NOT NULL REFERENCES backtest_runs (id) ON DELETE CASCADE,
    block_reason TEXT NOT NULL,
    blocked_entries INTEGER NOT NULL,
    first_blocked_at TIMESTAMPTZ,
    last_blocked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT backtest_blocked_entry_metrics_run_reason_key UNIQUE (backtest_run_id, block_reason),
    CONSTRAINT backtest_blocked_entry_metrics_block_reason_not_blank CHECK (btrim(block_reason) <> ''),
    CONSTRAINT backtest_blocked_entry_metrics_blocked_entries_non_negative CHECK (blocked_entries >= 0),
    CONSTRAINT backtest_blocked_entry_metrics_period_order CHECK (
        first_blocked_at IS NULL
        OR last_blocked_at IS NULL
        OR last_blocked_at >= first_blocked_at
    )
);

CREATE INDEX backtest_blocked_entry_metrics_reason_idx
    ON backtest_blocked_entry_metrics (block_reason);

COMMENT ON TABLE backtest_runs IS 'Backtest run metadata used to compare strategy variants and test periods.';
COMMENT ON TABLE backtest_artifacts IS 'Artifact gateway object keys for reports, plots, CSV files, and other backtest outputs.';
COMMENT ON TABLE backtest_summary_metrics IS 'One-row summary metrics for each backtest run.';
COMMENT ON TABLE backtest_weekly_metrics IS 'Weekly rollup metrics for backtest performance charts.';
COMMENT ON TABLE backtest_close_reason_metrics IS 'Per-run rollups grouped by trade close reason.';
COMMENT ON TABLE backtest_direction_metrics IS 'Per-run rollups grouped by trade direction.';
COMMENT ON TABLE backtest_blocked_entry_metrics IS 'Per-run rollups for blocked trade-entry decisions.';
