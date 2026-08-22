# GoldSight AI V3.0 — 数据库 Schema 设计文档

> 版本：V1.0 | 日期：2026-08-22 | 维护人：Database Agent

---

## 一、设计概述

### 1.1 数据库选型
- **引擎**：PostgreSQL 16（Docker 容器化部署）
- **容器名**：goldsight-postgres
- **端口**：5432
- **数据库名**：goldsight

### 1.2 设计原则
1. **数据可追溯**：所有表包含 `source`（来源）、`collected_at`（采集时间）、`quality_status`（质量状态）
2. **预测可追溯**：预测表包含 `agent_name`、`model_version`、`input_data_version`
3. **Migration 可重复**：所有 SQL 使用 `IF NOT EXISTS`，可安全重复执行
4. **时间序列优化**：索引按 `timestamp DESC` 设计，优化最新数据查询
5. **扩展性**：使用枚举类型 + JSONB 字段，支持未来新增数据类型无需改表

### 1.3 表总览

| 编号 | 表名 | 覆盖类别 | 说明 |
|------|------|----------|------|
| 1 | `data_sources` | 基础设施 | 数据源注册表 |
| 2 | `migration_versions` | 基础设施 | 迁移版本跟踪 |
| 3 | `gold_prices` | 类别1 | 黄金现货价格 |
| 4 | `gold_futures` | 类别1 | 黄金期货价格 |
| 5 | `precious_metals` | 类别13 | 白银、铂金、钯金 |
| 6 | `industrial_metals` | 类别14 | 铜铝锌镍铅锡 |
| 7 | `usd_data` | 类别5 | DXY 与主要货币对 |
| 8 | `treasury_yields` | 类别6 | 各期限国债收益率 |
| 9 | `oil_data` | 类别7 | WTI/Brent/库存/OPEC |
| 10 | `stock_market` | 类别8 | 主要指数与 VIX |
| 11 | `fed_events` | 类别2 | FOMC/利率/政策事件 |
| 12 | `economic_indicators` | 类别3+4 | 通胀+就业经济指标 |
| 13 | `gold_etf_flows` | 类别9 | ETF 资金流入流出 |
| 14 | `cftc_positions` | 类别9 | CFTC 持仓报告 |
| 15 | `central_bank_reserves` | 类别10 | 央行黄金储备 |
| 16 | `technical_indicators` | 类别12 | MA/RSI/MACD/布林带等 |
| 17 | `geopolitical_events` | 类别11 | 地缘政治事件 |
| 18 | `predictions_short_term` | 预测 | 短期预测（1h～5天） |
| 19 | `predictions_long_term` | 预测 | 长期预测（1～12月） |
| 20 | `ai_reports` | 报告 | AI 研究报告 |
| 21 | `data_quality_logs` | 质量 | 数据质量日志 |
| 22 | `data_snapshot_versions` | 追溯 | 数据快照版本 |

**合计：22 张表，覆盖全部 14 大类数据 + 预测/报告/质量管理**

---

## 二、表结构设计

### 2.1 通用字段规范

所有数据表均包含以下通用字段：

| 字段 | 类型 | 说明 |
|------|------|------|
| `source` | VARCHAR(100) | 数据来源标识 |
| `collected_at` | TIMESTAMPTZ | 数据采集时间 |
| `quality_status` | quality_status_t | 质量状态枚举 |
| `created_at` | TIMESTAMPTZ | 记录创建时间 |
| `updated_at` | TIMESTAMPTZ | 记录更新时间 |

### 2.2 自定义枚举类型

| 类型名 | 可选值 | 用途 |
|--------|--------|------|
| `quality_status_t` | pending, valid, warning, error, deprecated | 数据质量状态 |
| `prediction_horizon_t` | short_term, long_term | 预测时间范围 |
| `trend_direction_t` | bullish, neutral, bearish | 趋势方向 |
| `scenario_type_t` | bear, base, bull | 长期情景 |
| `data_frequency_t` | tick, minute, hourly, daily, weekly, monthly, quarterly, annual, event | 数据频率 |
| `data_category_t` | gold, fed, inflation, employment, usd, treasury, oil, stock, gold_fund, central_bank, geopolitical, technical, precious_metals, industrial_metals, prediction, report | 数据分类 |
| `report_type_t` | daily, weekly, monthly, special, ai_analysis | 报告类型 |
| `severity_level_t` | low, medium, high, critical | 严重程度 |
| `indicator_category_t` | trend, momentum, volatility, volume, support_resistance | 技术指标类别 |

### 2.3 各类别表设计要点

#### 类别 1：黄金行情（gold_prices + gold_futures）
- 现货表支持多种定价类型（spot/lbma_am/lbma_pm）
- 期货表按合约月份区分，含结算价和持仓量
- 唯一约束：`(timestamp, price_type/contract, symbol/exchange, source)`

#### 类别 2：美联储与利率（fed_events）
- 事件驱动设计，支持 FOMC 会议、利率决议、点阵图、政策声明、演讲等
- 使用 TEXT 字段存储政策声明全文
- `impact_level` 标记事件影响程度

#### 类别 3+4：通胀 + 就业经济（economic_indicators）
- 统一表设计，通过 `indicator_type` 区分 CPI/PCE/PPI/非农/GDP/PMI 等
- 支持 `actual_value`、`revised_value`（修正值）、`consensus`（市场预期）、`previous_value`（前值）
- `period` 字段支持月度（2024-01）和季度（2024Q1）格式

#### 类别 5：美元（usd_data）
- 通过 `pair` 字段区分 DXY 指数和各货币对
- 精度 6 位小数，满足汇率存储需求

#### 类别 6：美债（treasury_yields）
- 按期限（3M/1Y/2Y/5Y/10Y/30Y）分行存储
- 包含名义收益率、实际收益率（TIPS）、与 10Y 利差

#### 类别 7：原油（oil_data）
- 通过 `oil_type` 区分 WTI/Brent 价格、EIA 库存、OPEC 产量
- 库存和产量字段仅在对应类型时使用

#### 类别 8：美股与风险（stock_market）
- 覆盖 S&P 500、Nasdaq、道琼斯、VIX、GVZ（黄金波动率指数）

#### 类别 9：黄金资金面（gold_etf_flows + cftc_positions）
- ETF 表记录每日流入/流出（吨和美元）及总持仓
- CFTC 表记录管理资金多空持仓及变化

#### 类别 10：全球央行（central_bank_reserves）
- 按国家分行存储，支持购买/出售/持有操作
- 记录总储备量和黄金占外储比例

#### 类别 11：地缘政治（geopolitical_events）
- 事件驱动设计，支持战争/冲突/制裁/金融风险/选举/贸易争端
- 包含 `gold_impact` 评估对黄金的影响方向
- `countries` 使用数组类型存储涉及国家

#### 类别 12：技术面（technical_indicators）
- 通过 `indicator_name` + `period` 区分不同指标和周期
- `category` 按趋势/动量/波动/成交量/支撑阻力分类
- `extra_data` JSONB 存储附加参数

#### 类别 13：其他贵金属（precious_metals）
- 覆盖白银(XAG)、铂金(XPT)、钯金(XPD)
- 与黄金现货表结构一致，便于对比分析

#### 类别 14：工业金属（industrial_metals）
- 覆盖铜/铝/锌/镍/铅/锡
- 额外记录库存数据（吨）
- 支持多交易所（LME/SHFE/COMEX）

#### 预测表（predictions_short_term + predictions_long_term）
- 短期预测：趋势方向、概率分布、置信度、5 级支撑/阻力位、利多利空因素
- 长期预测：Bear/Base/Bull 三情景，各含概率和目标价区间
- 均包含 Agent 名称、模型版本、输入数据版本，确保完全可追溯

#### 报告表（ai_reports）
- 严格区分数据事实/模型输出/AI推断/不确定性
- 结论可追溯到具体数据和指标
- 关联预测 ID 列表

---

## 三、索引策略

### 3.1 设计思路
- **时间序列优先**：所有表以 `timestamp DESC` 为主索引方向
- **复合索引**：`(类别标识, timestamp DESC)` 优化分类查询
- **质量过滤**：`quality_status` 索引支持数据质量仪表盘
- **来源追溯**：`(source, timestamp DESC)` 支持数据源维度查询

### 3.2 索引统计
- 总索引数：约 75 个
- 覆盖所有 22 张表
- 包含单列索引和复合索引

### 3.3 索引分类

| 索引类型 | 数量 | 用途 |
|----------|------|------|
| 时间降序索引 | ~22 | 最新数据快速查询 |
| 类别+时间复合索引 | ~18 | 分类时间范围查询 |
| 质量状态索引 | ~20 | 数据质量监控 |
| 业务字段索引 | ~15 | 特定业务查询（如国家、事件类型等） |

---

## 四、扩展性设计

### 4.1 新增数据类型
- **方式 1**：在现有表中新增 `indicator_type`/`metal`/`pair` 等枚举值
- **方式 2**：创建新表，保持通用字段规范一致

### 4.2 JSONB 字段
- `config`、`extra_data`、`metadata` 等 JSONB 字段提供灵活扩展能力
- 支持存储任意结构化/半结构化数据

### 4.3 分区表（未来优化）
- 当单表数据量超过千万级时，可按时间范围进行表分区
- 推荐对 `gold_prices`、`economic_indicators`、`technical_indicators` 按月/年分区

---

## 五、Migration 文件清单

| 文件 | 说明 | 行数 |
|------|------|------|
| `migrations/V001__extensions_and_types.sql` | 扩展 + 9 个枚举类型 | 88 |
| `migrations/V002__create_tables.sql` | 22 张数据表 | 479 |
| `migrations/V003__create_indexes.sql` | ~75 个索引 | 138 |
| `init.sql` | 主入口脚本（按序执行 + 验证） | 60 |
