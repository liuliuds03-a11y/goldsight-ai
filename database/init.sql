-- ============================================================
-- GoldSight AI V3.0 - 数据库初始化主脚本
-- 按顺序执行所有 Migration，可重复执行
-- 执行方式：psql -U goldsight -d goldsight -f init.sql
-- ============================================================

\echo '============================================'
\echo 'GoldSight AI V3.0 - 数据库初始化开始'
\echo '============================================'

-- V001: 扩展与枚举类型
\echo '[1/3] 执行 V001 - 扩展与自定义枚举类型...'
\i migrations/V001__extensions_and_types.sql

-- V002: 创建所有数据表
\echo '[2/3] 执行 V002 - 创建数据表...'
\i migrations/V002__create_tables.sql

-- V003: 创建索引
\echo '[3/3] 执行 V003 - 创建索引...'
\i migrations/V003__create_indexes.sql

-- 记录迁移版本
INSERT INTO migration_versions (version, description)
VALUES
    ('V001', '扩展与自定义枚举类型'),
    ('V002', '创建所有数据表（22张表）'),
    ('V003', '创建索引（时间序列优化）')
ON CONFLICT (version) DO NOTHING;

-- 初始化默认数据源
INSERT INTO data_sources (source_name, source_type, category, provider, description)
VALUES
    ('manual', 'manual', 'gold', 'GoldSight', '手动录入数据'),
    ('api_placeholder', 'api', 'gold', 'GoldSight', 'API 数据源占位符，待配置')
ON CONFLICT (source_name) DO NOTHING;

\echo '============================================'
\echo 'GoldSight AI V3.0 - 数据库初始化完成'
\echo '============================================'

-- 验证
\echo ''
\echo '--- 验证：表数量 ---'
SELECT COUNT(*) AS total_tables FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE';

\echo '--- 验证：表清单 ---'
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
ORDER BY table_name;

\echo '--- 验证：索引数量 ---'
SELECT COUNT(*) AS total_indexes FROM pg_indexes
WHERE schemaname = 'public';

\echo '--- 验证：枚举类型 ---'
SELECT typname FROM pg_type
WHERE typtype = 'e'
ORDER BY typname;
