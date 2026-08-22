# GoldSight Database

GoldSight AI V3.0 数据库层，基于 **PostgreSQL 16**（通过 Docker 提供）。

## 职责

- 数据库 Schema 设计与 Migration 管理
- 结构化金融数据存储（行情、宏观数据、预测、报告等）
- 数据字典维护
- 索引优化与查询性能管理

## 设计原则

- 所有数据保留来源、时间戳和质量状态
- 预测结果可追溯（生成时间、输入数据版本、模型信息）
- Migration 可重复执行
- 本地通过 Docker 提供 PostgreSQL，避免污染主机环境

## 目录结构

```
database/
├── migrations/                                    # Migration SQL 脚本
│   ├── V001__extensions_and_types.sql            # 扩展 + 9 个枚举类型
│   ├── V002__create_tables.sql                   # 22 张数据表
│   └── V003__create_indexes.sql                  # ~75 个索引
├── init.sql                                       # 主入口脚本（按序执行全部 Migration）
├── schema-design.md                               # Schema 设计文档
├── data-dictionary.md                             # 数据字典
└── README.md                                      # 本文件
```

## 连接信息

参考项目根目录 `.env` 中的 PostgreSQL 配置：

- Host: `localhost:5432`
- Database: `goldsight`
- User: `goldsight`

## 快速执行

```bash
# 方式 1：通过 init.sql 一次性执行所有 Migration
Get-Content "database\init.sql" -Raw | docker exec -i goldsight-postgres psql -U goldsight -d goldsight

# 方式 2：单独执行某个 Migration
Get-Content "database\migrations\V001__extensions_and_types.sql" -Raw | docker exec -i goldsight-postgres psql -U goldsight -d goldsight
```

## 数据表总览（22 张）

| 编号 | 表名 | 覆盖类别 |
|------|------|----------|
| 1 | data_sources | 基础设施 |
| 2 | migration_versions | 基础设施 |
| 3 | gold_prices | 类别1-黄金现货 |
| 4 | gold_futures | 类别1-黄金期货 |
| 5 | precious_metals | 类别13-其他贵金属 |
| 6 | industrial_metals | 类别14-工业金属 |
| 7 | usd_data | 类别5-美元 |
| 8 | treasury_yields | 类别6-美债 |
| 9 | oil_data | 类别7-原油 |
| 10 | stock_market | 类别8-美股与风险 |
| 11 | fed_events | 类别2-美联储与利率 |
| 12 | economic_indicators | 类别3+4-通胀+就业经济 |
| 13 | gold_etf_flows | 类别9-ETF资金流 |
| 14 | cftc_positions | 类别9-CFTC持仓 |
| 15 | central_bank_reserves | 类别10-央行黄金储备 |
| 16 | technical_indicators | 类别12-技术指标 |
| 17 | geopolitical_events | 类别11-地缘政治 |
| 18 | predictions_short_term | 短期预测 |
| 19 | predictions_long_term | 长期预测 |
| 20 | ai_reports | AI研究报告 |
| 21 | data_quality_logs | 数据质量日志 |
| 22 | data_snapshot_versions | 数据快照版本 |
