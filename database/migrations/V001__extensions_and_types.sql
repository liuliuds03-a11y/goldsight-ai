-- ============================================================
-- GoldSight AI V3.0 - Migration V001
-- 扩展与自定义枚举类型
-- 可重复执行（IF NOT EXISTS）
-- ============================================================

BEGIN;

-- ============================================================
-- 1. PostgreSQL 扩展
-- ============================================================
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";       -- UUID 生成
CREATE EXTENSION IF NOT EXISTS "pg_trgm";         -- 模糊文本搜索
CREATE EXTENSION IF NOT EXISTS "btree_gin";       -- GIN 索引支持 B-tree 类型

-- ============================================================
-- 2. 自定义枚举类型
-- ============================================================

-- 数据质量状态
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'quality_status_t') THEN
        CREATE TYPE quality_status_t AS ENUM ('pending', 'valid', 'warning', 'error', 'deprecated');
    END IF;
END $$;

-- 预测时间范围
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'prediction_horizon_t') THEN
        CREATE TYPE prediction_horizon_t AS ENUM ('short_term', 'long_term');
    END IF;
END $$;

-- 预测趋势方向
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'trend_direction_t') THEN
        CREATE TYPE trend_direction_t AS ENUM ('bullish', 'neutral', 'bearish');
    END IF;
END $$;

-- 预测情景类型
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'scenario_type_t') THEN
        CREATE TYPE scenario_type_t AS ENUM ('bear', 'base', 'bull');
    END IF;
END $$;

-- 数据频率
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'data_frequency_t') THEN
        CREATE TYPE data_frequency_t AS ENUM ('tick', 'minute', 'hourly', 'daily', 'weekly', 'monthly', 'quarterly', 'annual', 'event');
    END IF;
END $$;

-- 数据分类
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'data_category_t') THEN
        CREATE TYPE data_category_t AS ENUM (
            'gold', 'fed', 'inflation', 'employment', 'usd',
            'treasury', 'oil', 'stock', 'gold_fund', 'central_bank',
            'geopolitical', 'technical', 'precious_metals', 'industrial_metals',
            'prediction', 'report'
        );
    END IF;
END $$;

-- 报告类型
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'report_type_t') THEN
        CREATE TYPE report_type_t AS ENUM ('daily', 'weekly', 'monthly', 'special', 'ai_analysis');
    END IF;
END $$;

-- 事件严重程度
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'severity_level_t') THEN
        CREATE TYPE severity_level_t AS ENUM ('low', 'medium', 'high', 'critical');
    END IF;
END $$;

-- 指标类别（用于技术指标）
DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'indicator_category_t') THEN
        CREATE TYPE indicator_category_t AS ENUM ('trend', 'momentum', 'volatility', 'volume', 'support_resistance');
    END IF;
END $$;

COMMIT;
