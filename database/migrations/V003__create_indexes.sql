-- ============================================================
-- GoldSight AI V3.0 - Migration V003
-- 索引策略（针对时间序列查询优化）
-- 可重复执行（IF NOT EXISTS 通过 CONCURRENTLY 安全创建）
-- ============================================================

BEGIN;

-- ============================================================
-- 通用：所有时间序列表按 timestamp 降序查询优化
-- ============================================================

-- gold_prices
CREATE INDEX IF NOT EXISTS idx_gold_prices_timestamp ON gold_prices (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_gold_prices_symbol_ts ON gold_prices (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_gold_prices_collected ON gold_prices (collected_at DESC);
CREATE INDEX IF NOT EXISTS idx_gold_prices_quality ON gold_prices (quality_status);

-- gold_futures
CREATE INDEX IF NOT EXISTS idx_gold_futures_timestamp ON gold_futures (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_gold_futures_contract ON gold_futures (contract, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_gold_futures_quality ON gold_futures (quality_status);

-- precious_metals
CREATE INDEX IF NOT EXISTS idx_precious_metals_timestamp ON precious_metals (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_precious_metals_metal_ts ON precious_metals (metal, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_precious_metals_quality ON precious_metals (quality_status);

-- industrial_metals
CREATE INDEX IF NOT EXISTS idx_industrial_metals_timestamp ON industrial_metals (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_industrial_metals_metal_ts ON industrial_metals (metal, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_industrial_metals_quality ON industrial_metals (quality_status);

-- usd_data
CREATE INDEX IF NOT EXISTS idx_usd_data_timestamp ON usd_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_usd_data_pair_ts ON usd_data (pair, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_usd_data_quality ON usd_data (quality_status);

-- treasury_yields
CREATE INDEX IF NOT EXISTS idx_treasury_yields_timestamp ON treasury_yields (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_treasury_yields_maturity_ts ON treasury_yields (maturity, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_treasury_yields_quality ON treasury_yields (quality_status);

-- oil_data
CREATE INDEX IF NOT EXISTS idx_oil_data_timestamp ON oil_data (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_oil_data_type_ts ON oil_data (oil_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_oil_data_quality ON oil_data (quality_status);

-- stock_market
CREATE INDEX IF NOT EXISTS idx_stock_market_timestamp ON stock_market (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stock_market_symbol_ts ON stock_market (index_symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_stock_market_quality ON stock_market (quality_status);

-- fed_events
CREATE INDEX IF NOT EXISTS idx_fed_events_date ON fed_events (event_date DESC);
CREATE INDEX IF NOT EXISTS idx_fed_events_type ON fed_events (event_type);
CREATE INDEX IF NOT EXISTS idx_fed_events_impact ON fed_events (impact_level);
CREATE INDEX IF NOT EXISTS idx_fed_events_quality ON fed_events (quality_status);

-- economic_indicators
CREATE INDEX IF NOT EXISTS idx_economic_indicators_timestamp ON economic_indicators (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_economic_indicators_type_ts ON economic_indicators (indicator_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_economic_indicators_period ON economic_indicators (period);
CREATE INDEX IF NOT EXISTS idx_economic_indicators_quality ON economic_indicators (quality_status);

-- gold_etf_flows
CREATE INDEX IF NOT EXISTS idx_gold_etf_timestamp ON gold_etf_flows (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_gold_etf_name_ts ON gold_etf_flows (etf_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_gold_etf_quality ON gold_etf_flows (quality_status);

-- cftc_positions
CREATE INDEX IF NOT EXISTS idx_cftc_timestamp ON cftc_positions (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_cftc_quality ON cftc_positions (quality_status);

-- central_bank_reserves
CREATE INDEX IF NOT EXISTS idx_central_bank_timestamp ON central_bank_reserves (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_central_bank_country_ts ON central_bank_reserves (country, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_central_bank_action ON central_bank_reserves (action);
CREATE INDEX IF NOT EXISTS idx_central_bank_quality ON central_bank_reserves (quality_status);

-- technical_indicators
CREATE INDEX IF NOT EXISTS idx_tech_indicators_timestamp ON technical_indicators (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tech_indicators_symbol_ts ON technical_indicators (symbol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_tech_indicators_name ON technical_indicators (indicator_name);
CREATE INDEX IF NOT EXISTS idx_tech_indicators_category ON technical_indicators (category);
CREATE INDEX IF NOT EXISTS idx_tech_indicators_quality ON technical_indicators (quality_status);

-- geopolitical_events
CREATE INDEX IF NOT EXISTS idx_geo_events_date ON geopolitical_events (event_date DESC);
CREATE INDEX IF NOT EXISTS idx_geo_events_type ON geopolitical_events (event_type);
CREATE INDEX IF NOT EXISTS idx_geo_events_severity ON geopolitical_events (severity);
CREATE INDEX IF NOT EXISTS idx_geo_events_region ON geopolitical_events (region);
CREATE INDEX IF NOT EXISTS idx_geo_events_status ON geopolitical_events (status);
CREATE INDEX IF NOT EXISTS idx_geo_events_gold_impact ON geopolitical_events (gold_impact);
CREATE INDEX IF NOT EXISTS idx_geo_events_quality ON geopolitical_events (quality_status);

-- predictions_short_term
CREATE INDEX IF NOT EXISTS idx_pred_short_generated ON predictions_short_term (generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_pred_short_symbol ON predictions_short_term (symbol, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_pred_short_agent ON predictions_short_term (agent_name);
CREATE INDEX IF NOT EXISTS idx_pred_short_quality ON predictions_short_term (quality_status);

-- predictions_long_term
CREATE INDEX IF NOT EXISTS idx_pred_long_generated ON predictions_long_term (generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_pred_long_symbol ON predictions_long_term (symbol, generated_at DESC);
CREATE INDEX IF NOT EXISTS idx_pred_long_scenario ON predictions_long_term (scenario);
CREATE INDEX IF NOT EXISTS idx_pred_long_agent ON predictions_long_term (agent_name);
CREATE INDEX IF NOT EXISTS idx_pred_long_quality ON predictions_long_term (quality_status);

-- ai_reports
CREATE INDEX IF NOT EXISTS idx_reports_date ON ai_reports (report_date DESC);
CREATE INDEX IF NOT EXISTS idx_reports_type ON ai_reports (report_type);
CREATE INDEX IF NOT EXISTS idx_reports_agent ON ai_reports (agent_name);
CREATE INDEX IF NOT EXISTS idx_reports_quality ON ai_reports (quality_status);

-- data_quality_logs
CREATE INDEX IF NOT EXISTS idx_quality_logs_timestamp ON data_quality_logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_quality_logs_table ON data_quality_logs (table_name);
CREATE INDEX IF NOT EXISTS idx_quality_logs_severity ON data_quality_logs (severity);
CREATE INDEX IF NOT EXISTS idx_quality_logs_resolved ON data_quality_logs (resolved);
CREATE INDEX IF NOT EXISTS idx_quality_logs_check_type ON data_quality_logs (check_type);

-- data_snapshot_versions
CREATE INDEX IF NOT EXISTS idx_snapshot_date ON data_snapshot_versions (snapshot_date DESC);

-- ============================================================
-- 复合索引：高频查询场景优化
-- ============================================================

-- 按时间范围 + 质量状态查询（数据质量仪表盘）
CREATE INDEX IF NOT EXISTS idx_gold_prices_ts_quality ON gold_prices (timestamp DESC, quality_status);
CREATE INDEX IF NOT EXISTS idx_economic_ts_quality ON economic_indicators (timestamp DESC, quality_status);

-- 按来源 + 时间查询（数据源追溯）
CREATE INDEX IF NOT EXISTS idx_gold_prices_source_ts ON gold_prices (source, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_economic_source_ts ON economic_indicators (source, timestamp DESC);

COMMIT;
