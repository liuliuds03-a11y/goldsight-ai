-- ============================================================
-- GoldSight AI V3.0 - Migration V004
-- 创建跨市场关联与宏观分析结果存储表
-- 可重复执行（IF NOT EXISTS）
-- ============================================================

BEGIN;

-- ============================================================
-- 分析结果表 — 存储跨市场关联分析和宏观面分析结果
-- ============================================================
CREATE TABLE IF NOT EXISTS analysis_results (
    id              BIGSERIAL PRIMARY KEY,
    analysis_type   VARCHAR(30) NOT NULL,           -- market_correlation, macro
    generated_at    TIMESTAMPTZ NOT NULL,
    conclusion      VARCHAR(20) NOT NULL,           -- 利多, 利空, 中性
    confidence      NUMERIC(6,4) NOT NULL,          -- 0.0 ~ 1.0
    score           NUMERIC(6,2) NOT NULL,          -- -100 ~ +100
    factors         JSONB NOT NULL DEFAULT '[]',    -- 各因素分析详情
    data_range      JSONB NOT NULL DEFAULT '{}',    -- 输入数据时间范围
    source          VARCHAR(100) NOT NULL DEFAULT 'market_macro_agent',
    metadata        JSONB DEFAULT '{}',             -- 附加信息（滚动相关系数等）
    collected_at    TIMESTAMPTZ DEFAULT NOW(),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- 按分析类型查询最新记录的索引
CREATE INDEX IF NOT EXISTS idx_analysis_results_type_latest
    ON analysis_results (analysis_type, generated_at DESC);

-- 按生成时间查询
CREATE INDEX IF NOT EXISTS idx_analysis_results_generated
    ON analysis_results (generated_at DESC);

COMMIT;
