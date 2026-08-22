-- ============================================================
-- GoldSight AI V3.0 - Migration V002
-- 创建所有数据表（22 张表，覆盖 14 大类 + 基础设施）
-- 可重复执行（IF NOT EXISTS）
-- ============================================================

BEGIN;

-- ============================================================
-- 基础设施表
-- ============================================================

-- 数据源注册表
CREATE TABLE IF NOT EXISTS data_sources (
    id              SERIAL PRIMARY KEY,
    source_name     VARCHAR(100) NOT NULL UNIQUE,
    source_type     VARCHAR(50) NOT NULL,           -- api, web_scrape, manual, file
    category        data_category_t NOT NULL,
    provider        VARCHAR(200),
    base_url        TEXT,
    description     TEXT,
    is_active       BOOLEAN DEFAULT TRUE,
    config          JSONB DEFAULT '{}',             -- 连接配置（不含密钥）
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 迁移版本跟踪
CREATE TABLE IF NOT EXISTS migration_versions (
    version         VARCHAR(50) PRIMARY KEY,
    description     TEXT,
    applied_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 类别 1：黄金行情 — 现货价格
-- ============================================================
CREATE TABLE IF NOT EXISTS gold_prices (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    price_type      VARCHAR(20) NOT NULL DEFAULT 'spot',  -- spot, lbma_am, lbma_pm
    symbol          VARCHAR(20) NOT NULL DEFAULT 'XAUUSD',
    open            NUMERIC(12,4),
    high            NUMERIC(12,4),
    low             NUMERIC(12,4),
    close           NUMERIC(12,4),
    change_value    NUMERIC(12,4),
    change_pct      NUMERIC(8,4),
    volume          BIGINT,
    open_interest   BIGINT,
    volatility      NUMERIC(8,4),                 -- 隐含波动率 %
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, price_type, symbol, source)
);

-- 类别 1：黄金行情 — 期货价格
CREATE TABLE IF NOT EXISTS gold_futures (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    contract        VARCHAR(20) NOT NULL,          -- 合约月份 如 202412
    exchange        VARCHAR(20) DEFAULT 'COMEX',
    open            NUMERIC(12,4),
    high            NUMERIC(12,4),
    low             NUMERIC(12,4),
    close           NUMERIC(12,4),
    settle          NUMERIC(12,4),                 -- 结算价
    change_value    NUMERIC(12,4),
    change_pct      NUMERIC(8,4),
    volume          BIGINT,
    open_interest   BIGINT,
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, contract, exchange, source)
);

-- ============================================================
-- 类别 13：其他贵金属 — 白银、铂金、钯金
-- ============================================================
CREATE TABLE IF NOT EXISTS precious_metals (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    metal           VARCHAR(20) NOT NULL,          -- silver, platinum, palladium
    symbol          VARCHAR(20) NOT NULL,          -- XAGUSD, XPTUSD, XPDUSD
    open            NUMERIC(12,4),
    high            NUMERIC(12,4),
    low             NUMERIC(12,4),
    close           NUMERIC(12,4),
    change_value    NUMERIC(12,4),
    change_pct      NUMERIC(8,4),
    volume          BIGINT,
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, metal, symbol, source)
);

-- ============================================================
-- 类别 14：工业金属 — 铜、铝、锌、镍、铅、锡
-- ============================================================
CREATE TABLE IF NOT EXISTS industrial_metals (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    metal           VARCHAR(20) NOT NULL,          -- copper, aluminum, zinc, nickel, lead, tin
    symbol          VARCHAR(20) NOT NULL,
    exchange        VARCHAR(30),                   -- LME, SHFE, COMEX
    open            NUMERIC(12,4),
    high            NUMERIC(12,4),
    low             NUMERIC(12,4),
    close           NUMERIC(12,4),
    change_value    NUMERIC(12,4),
    change_pct      NUMERIC(8,4),
    volume          BIGINT,
    inventory       NUMERIC(16,2),                 -- 库存量（吨）
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, metal, exchange, source)
);

-- ============================================================
-- 类别 5：美元 — DXY 与主要货币对
-- ============================================================
CREATE TABLE IF NOT EXISTS usd_data (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    pair            VARCHAR(20) NOT NULL,          -- DXY, EURUSD, USDJPY, USDCNH, GBPUSD, AUDUSD
    open            NUMERIC(12,6),
    high            NUMERIC(12,6),
    low             NUMERIC(12,6),
    close           NUMERIC(12,6),
    change_value    NUMERIC(12,6),
    change_pct      NUMERIC(8,4),
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, pair, source)
);

-- ============================================================
-- 类别 6：美债 — 各期限收益率、TIPS、实际收益率
-- ============================================================
CREATE TABLE IF NOT EXISTS treasury_yields (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    maturity        VARCHAR(10) NOT NULL,          -- 3M, 1Y, 2Y, 5Y, 10Y, 30Y
    yield           NUMERIC(8,4),                  -- 名义收益率 %
    real_yield      NUMERIC(8,4),                  -- 实际收益率 %（TIPS）
    spread_to_10y   NUMERIC(8,4),                  -- 与 10Y 的利差
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, maturity, source)
);

-- ============================================================
-- 类别 7：原油 — WTI、Brent、库存、OPEC
-- ============================================================
CREATE TABLE IF NOT EXISTS oil_data (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    oil_type        VARCHAR(20) NOT NULL,          -- wti, brent, eia_inventory, opec_crude
    open            NUMERIC(10,2),
    high            NUMERIC(10,2),
    low             NUMERIC(10,2),
    close           NUMERIC(10,2),
    change_value    NUMERIC(10,2),
    change_pct      NUMERIC(8,4),
    volume          BIGINT,
    inventory_bbl   BIGINT,                        -- 库存（桶）, 仅 eia_inventory
    opec_production NUMERIC(12,2),                 -- OPEC 产量（千桶/日）, 仅 opec_crude
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, oil_type, source)
);

-- ============================================================
-- 类别 8：美股与风险 — 主要指数、VIX
-- ============================================================
CREATE TABLE IF NOT EXISTS stock_market (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    index_symbol    VARCHAR(20) NOT NULL,          -- SPX, NDX, DJI, VIX, GVZ
    open            NUMERIC(14,4),
    high            NUMERIC(14,4),
    low             NUMERIC(14,4),
    close           NUMERIC(14,4),
    change_value    NUMERIC(14,4),
    change_pct      NUMERIC(8,4),
    volume          BIGINT,
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, index_symbol, source)
);

-- ============================================================
-- 类别 2：美联储与利率 — FOMC、利率、政策事件
-- ============================================================
CREATE TABLE IF NOT EXISTS fed_events (
    id              BIGSERIAL PRIMARY KEY,
    event_date      TIMESTAMPTZ NOT NULL,
    event_type      VARCHAR(50) NOT NULL,          -- fomc_meeting, rate_decision, dot_plot, policy_statement, speech
    fed_funds_rate  NUMERIC(6,4),                  -- 联邦基金利率 %
    target_range_low NUMERIC(6,4),                 -- 目标区间下限
    target_range_high NUMERIC(6,4),                -- 目标区间上限
    dot_plot_median NUMERIC(6,4),                  -- 点阵图中位数
    title           VARCHAR(300),
    summary         TEXT,
    full_text       TEXT,
    impact_level    severity_level_t,
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 类别 3 & 4：通胀 + 就业与经济 — 统一经济指标表
-- ============================================================
CREATE TABLE IF NOT EXISTS economic_indicators (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    indicator_type  VARCHAR(50) NOT NULL,          -- cpi, core_cpi, pce, ppi, inflation_expectation,
                                                   -- nonfarm, unemployment, gdp, pmi, retail_sales
    period          VARCHAR(20),                   -- 数据周期 如 2024-01, 2024Q1
    actual_value    NUMERIC(14,4),                 -- 实际公布值
    revised_value   NUMERIC(14,4),                 -- 修正值
    consensus       NUMERIC(14,4),                 -- 市场预期值
    previous_value  NUMERIC(14,4),                 -- 前值
    unit            VARCHAR(20),                   -- %, 千人, 十亿美元 等
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, indicator_type, period, source)
);

-- ============================================================
-- 类别 9：黄金资金面 — ETF 流入流出
-- ============================================================
CREATE TABLE IF NOT EXISTS gold_etf_flows (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    etf_name        VARCHAR(50) NOT NULL,          -- GLD, IAU, SPDR, etc.
    flow_tons       NUMERIC(14,4),                 -- 当日流入（正）/流出（负）吨
    flow_usd        NUMERIC(16,2),                 -- 当日流入/流出金额（美元）
    total_holdings_tons NUMERIC(16,4),             -- 总持仓（吨）
    total_holdings_usd  NUMERIC(18,2),             -- 总持仓（美元）
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, etf_name, source)
);

-- 类别 9：黄金资金面 — CFTC 持仓
CREATE TABLE IF NOT EXISTS cftc_positions (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,          -- 报告截止日期（每周五）
    report_type     VARCHAR(50) DEFAULT 'gold',
    managed_money_long  BIGINT,
    managed_money_short BIGINT,
    managed_money_net   BIGINT,
    total_long      BIGINT,
    total_short     BIGINT,
    total_net       BIGINT,
    change_long     BIGINT,
    change_short    BIGINT,
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, report_type, source)
);

-- ============================================================
-- 类别 10：全球央行 — 黄金储备变化
-- ============================================================
CREATE TABLE IF NOT EXISTS central_bank_reserves (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    country         VARCHAR(100) NOT NULL,
    bank_name       VARCHAR(200),
    action          VARCHAR(20) NOT NULL,          -- purchase, sale, hold
    volume_tons     NUMERIC(14,4),                 -- 交易/变化量（吨）
    total_reserves_tons NUMERIC(16,4),             -- 总储备（吨）
    reserves_pct    NUMERIC(6,2),                  -- 黄金占外储比例 %
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, country, source)
);

-- ============================================================
-- 类别 12：技术面 — MA/RSI/MACD/布林带/ADX/Fibonacci
-- ============================================================
CREATE TABLE IF NOT EXISTS technical_indicators (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    symbol          VARCHAR(20) NOT NULL,          -- XAUUSD, XAGUSD 等
    indicator_name  VARCHAR(30) NOT NULL,          -- sma, ema, rsi, macd, macd_signal, macd_hist,
                                                   -- bollinger_upper, bollinger_mid, bollinger_lower,
                                                   -- adx, fibonacci_level
    period          INTEGER,                       -- 计算周期（如 14, 20, 50, 200）
    category        indicator_category_t,          -- trend, momentum, volatility, volume, support_resistance
    value           NUMERIC(14,6),
    extra_data      JSONB DEFAULT '{}',            -- 附加参数（如布林带宽度、MACD 快慢线等）
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(timestamp, symbol, indicator_name, period, source)
);

-- ============================================================
-- 类别 11：地缘政治 — 事件记录
-- ============================================================
CREATE TABLE IF NOT EXISTS geopolitical_events (
    id              BIGSERIAL PRIMARY KEY,
    event_date      TIMESTAMPTZ NOT NULL,
    event_type      VARCHAR(50) NOT NULL,          -- war, conflict, sanction, financial_risk, election, trade_dispute
    title           VARCHAR(500) NOT NULL,
    description     TEXT,
    region          VARCHAR(100),
    countries       TEXT[],                         -- 涉及国家列表
    severity        severity_level_t,
    gold_impact     VARCHAR(20),                   -- bullish, bearish, neutral
    gold_impact_detail TEXT,
    status          VARCHAR(20) DEFAULT 'ongoing', -- ongoing, resolved, escalated
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 预测表 — 短期预测（1小时～5天）
-- ============================================================
CREATE TABLE IF NOT EXISTS predictions_short_term (
    id              BIGSERIAL PRIMARY KEY,
    generated_at    TIMESTAMPTZ NOT NULL,
    symbol          VARCHAR(20) NOT NULL DEFAULT 'XAUUSD',
    trend           trend_direction_t,             -- bullish, neutral, bearish
    probability_up  NUMERIC(6,4),                  -- 上涨概率
    probability_down NUMERIC(6,4),                 -- 下跌概率
    probability_sideways NUMERIC(6,4),             -- 震荡概率
    confidence      NUMERIC(6,4),                  -- 置信度
    support_levels  JSONB,                         -- S1-S5 含依据 [{"level":2050,"reason":"..."}]
    resistance_levels JSONB,                       -- R1-R5 含依据
    bullish_factors JSONB,                         -- 利多因素列表
    bearish_factors JSONB,                         -- 利空因素列表
    invalidation_condition TEXT,                   -- 预测失效条件
    agent_name      VARCHAR(100),                  -- 生成预测的 Agent
    model_version   VARCHAR(50),                   -- 模型版本
    input_data_version VARCHAR(100),               -- 输入数据版本
    metadata        JSONB DEFAULT '{}',
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 预测表 — 长期预测（1～12个月）
CREATE TABLE IF NOT EXISTS predictions_long_term (
    id              BIGSERIAL PRIMARY KEY,
    generated_at    TIMESTAMPTZ NOT NULL,
    symbol          VARCHAR(20) NOT NULL DEFAULT 'XAUUSD',
    scenario        scenario_type_t NOT NULL,      -- bear, base, bull
    probability     NUMERIC(6,4),                  -- 情景概率
    target_price_low NUMERIC(12,4),                -- 目标价下限
    target_price_high NUMERIC(12,4),               -- 目标价上限
    target_price_mid NUMERIC(12,4),                -- 目标价中位
    core_drivers    JSONB,                         -- 核心驱动因素
    risks           JSONB,                         -- 风险因素
    time_horizon_months INTEGER,                   -- 预测时间跨度（月）
    agent_name      VARCHAR(100),
    model_version   VARCHAR(50),
    input_data_version VARCHAR(100),
    metadata        JSONB DEFAULT '{}',
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- AI 研究报告
-- ============================================================
CREATE TABLE IF NOT EXISTS ai_reports (
    id              BIGSERIAL PRIMARY KEY,
    report_date     TIMESTAMPTZ NOT NULL,
    report_type     report_type_t NOT NULL,        -- daily, weekly, monthly, special, ai_analysis
    title           VARCHAR(500) NOT NULL,
    summary         TEXT,
    content         TEXT,                          -- 报告全文（Markdown）
    data_facts      JSONB,                         -- 数据事实部分
    model_outputs   JSONB,                         -- 模型输出部分
    ai_inferences   JSONB,                         -- AI 推断部分
    uncertainties   JSONB,                         -- 不确定性说明
    conclusions     JSONB,                         -- 结论（可追溯到数据和指标）
    agent_name      VARCHAR(100),
    model_version   VARCHAR(50),
    input_data_version VARCHAR(100),
    prediction_ids  BIGINT[],                      -- 关联的预测 ID
    metadata        JSONB DEFAULT '{}',
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 数据质量日志
-- ============================================================
CREATE TABLE IF NOT EXISTS data_quality_logs (
    id              BIGSERIAL PRIMARY KEY,
    timestamp       TIMESTAMPTZ NOT NULL,
    table_name      VARCHAR(100) NOT NULL,
    record_id       BIGINT,
    check_type      VARCHAR(50) NOT NULL,          -- completeness, accuracy, timeliness, consistency, validity
    severity        severity_level_t NOT NULL,
    message         TEXT NOT NULL,
    details         JSONB DEFAULT '{}',
    resolved        BOOLEAN DEFAULT FALSE,
    resolved_at     TIMESTAMPTZ,
    source          VARCHAR(100) NOT NULL,
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    quality_status  quality_status_t DEFAULT 'pending',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 数据快照版本（预测追溯用）
-- ============================================================
CREATE TABLE IF NOT EXISTS data_snapshot_versions (
    id              BIGSERIAL PRIMARY KEY,
    snapshot_date   DATE NOT NULL,
    version_tag     VARCHAR(100) NOT NULL UNIQUE,  -- 如 v20240822
    description     TEXT,
    table_counts    JSONB,                         -- 各表记录数 {"gold_prices": 1000, ...}
    data_summary    JSONB,                         -- 数据摘要统计
    is_valid        BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

COMMIT;
