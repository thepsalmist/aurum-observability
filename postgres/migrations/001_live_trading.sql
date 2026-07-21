CREATE TABLE bot_heartbeats (
    id BIGSERIAL PRIMARY KEY,
    bot_id TEXT NOT NULL,
    magic BIGINT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    status TEXT NOT NULL,
    message TEXT,
    observed_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT bot_heartbeats_bot_id_not_blank CHECK (btrim(bot_id) <> ''),
    CONSTRAINT bot_heartbeats_symbol_not_blank CHECK (btrim(symbol) <> ''),
    CONSTRAINT bot_heartbeats_timeframe_not_blank CHECK (btrim(timeframe) <> ''),
    CONSTRAINT bot_heartbeats_status_not_blank CHECK (btrim(status) <> '')
);

CREATE INDEX bot_heartbeats_bot_observed_at_idx
    ON bot_heartbeats (bot_id, observed_at DESC);

CREATE INDEX bot_heartbeats_symbol_timeframe_observed_at_idx
    ON bot_heartbeats (symbol, timeframe, observed_at DESC);

CREATE TABLE account_snapshots (
    id BIGSERIAL PRIMARY KEY,
    bot_id TEXT NOT NULL,
    account_id TEXT,
    balance DOUBLE PRECISION,
    equity DOUBLE PRECISION,
    margin DOUBLE PRECISION,
    free_margin DOUBLE PRECISION,
    profit DOUBLE PRECISION,
    observed_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT account_snapshots_bot_id_not_blank CHECK (btrim(bot_id) <> ''),
    CONSTRAINT account_snapshots_account_id_not_blank CHECK (account_id IS NULL OR btrim(account_id) <> '')
);

CREATE INDEX account_snapshots_bot_observed_at_idx
    ON account_snapshots (bot_id, observed_at DESC);

CREATE INDEX account_snapshots_account_observed_at_idx
    ON account_snapshots (account_id, observed_at DESC)
    WHERE account_id IS NOT NULL;

CREATE TABLE trade_events (
    id BIGSERIAL PRIMARY KEY,
    bot_id TEXT NOT NULL,
    magic BIGINT NOT NULL,
    symbol TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    event_type TEXT NOT NULL,
    direction TEXT,
    mt5_position_ticket BIGINT,
    mt5_deal_ticket BIGINT,
    entry_price DOUBLE PRECISION,
    exit_price DOUBLE PRECISION,
    sl DOUBLE PRECISION,
    tp DOUBLE PRECISION,
    volume DOUBLE PRECISION,
    profit DOUBLE PRECISION,
    reason TEXT,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT trade_events_bot_id_not_blank CHECK (btrim(bot_id) <> ''),
    CONSTRAINT trade_events_symbol_not_blank CHECK (btrim(symbol) <> ''),
    CONSTRAINT trade_events_timeframe_not_blank CHECK (btrim(timeframe) <> ''),
    CONSTRAINT trade_events_event_type_not_blank CHECK (btrim(event_type) <> ''),
    CONSTRAINT trade_events_direction_not_blank CHECK (direction IS NULL OR btrim(direction) <> ''),
    CONSTRAINT trade_events_reason_not_blank CHECK (reason IS NULL OR btrim(reason) <> ''),
    CONSTRAINT trade_events_payload_is_object CHECK (jsonb_typeof(payload) = 'object'),
    CONSTRAINT trade_events_volume_positive CHECK (volume IS NULL OR volume > 0)
);

CREATE INDEX trade_events_bot_occurred_at_idx
    ON trade_events (bot_id, occurred_at DESC);

CREATE INDEX trade_events_symbol_timeframe_occurred_at_idx
    ON trade_events (symbol, timeframe, occurred_at DESC);

CREATE INDEX trade_events_event_type_occurred_at_idx
    ON trade_events (event_type, occurred_at DESC);

CREATE INDEX trade_events_position_ticket_idx
    ON trade_events (mt5_position_ticket, occurred_at DESC)
    WHERE mt5_position_ticket IS NOT NULL;

CREATE INDEX trade_events_deal_ticket_idx
    ON trade_events (mt5_deal_ticket, occurred_at DESC)
    WHERE mt5_deal_ticket IS NOT NULL;

CREATE TABLE open_position_snapshots (
    id BIGSERIAL PRIMARY KEY,
    bot_id TEXT NOT NULL,
    magic BIGINT NOT NULL,
    symbol TEXT NOT NULL,
    mt5_position_ticket BIGINT NOT NULL,
    direction TEXT NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    entry_price DOUBLE PRECISION NOT NULL,
    current_price DOUBLE PRECISION,
    sl DOUBLE PRECISION,
    tp DOUBLE PRECISION,
    floating_profit DOUBLE PRECISION,
    observed_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT open_position_snapshots_bot_id_not_blank CHECK (btrim(bot_id) <> ''),
    CONSTRAINT open_position_snapshots_symbol_not_blank CHECK (btrim(symbol) <> ''),
    CONSTRAINT open_position_snapshots_direction_not_blank CHECK (btrim(direction) <> ''),
    CONSTRAINT open_position_snapshots_volume_positive CHECK (volume > 0)
);

CREATE INDEX open_position_snapshots_bot_observed_at_idx
    ON open_position_snapshots (bot_id, observed_at DESC);

CREATE INDEX open_position_snapshots_symbol_observed_at_idx
    ON open_position_snapshots (symbol, observed_at DESC);

CREATE INDEX open_position_snapshots_ticket_observed_at_idx
    ON open_position_snapshots (mt5_position_ticket, observed_at DESC);

CREATE TABLE daily_risk_snapshots (
    id BIGSERIAL PRIMARY KEY,
    bot_id TEXT NOT NULL,
    magic BIGINT NOT NULL,
    symbol TEXT NOT NULL,
    trade_date DATE NOT NULL,
    wins INTEGER NOT NULL,
    losses INTEGER NOT NULL,
    trades INTEGER NOT NULL,
    circuit_breaker_active BOOLEAN NOT NULL,
    observed_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT daily_risk_snapshots_bot_id_not_blank CHECK (btrim(bot_id) <> ''),
    CONSTRAINT daily_risk_snapshots_symbol_not_blank CHECK (btrim(symbol) <> ''),
    CONSTRAINT daily_risk_snapshots_wins_non_negative CHECK (wins >= 0),
    CONSTRAINT daily_risk_snapshots_losses_non_negative CHECK (losses >= 0),
    CONSTRAINT daily_risk_snapshots_trades_non_negative CHECK (trades >= 0),
    CONSTRAINT daily_risk_snapshots_trades_covers_results CHECK (trades >= wins + losses)
);

CREATE INDEX daily_risk_snapshots_bot_trade_date_observed_at_idx
    ON daily_risk_snapshots (bot_id, trade_date DESC, observed_at DESC);

CREATE INDEX daily_risk_snapshots_symbol_trade_date_observed_at_idx
    ON daily_risk_snapshots (symbol, trade_date DESC, observed_at DESC);

COMMENT ON TABLE bot_heartbeats IS 'Append-only bot runtime heartbeat and status observations.';
COMMENT ON TABLE account_snapshots IS 'Append-only account balance, equity, margin, and profit observations.';
COMMENT ON TABLE trade_events IS 'Append-only trade, order failure, broker error, and lifecycle events published by trading runtimes.';
COMMENT ON TABLE open_position_snapshots IS 'Append-only snapshots of currently open positions observed by trading runtimes.';
COMMENT ON TABLE daily_risk_snapshots IS 'Append-only daily risk counter and circuit-breaker observations.';
