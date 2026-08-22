# GoldSight AI V3.0 — 数据字典

> 版本：V1.0 | 日期：2026-08-22 | 维护人：Database Agent

---

## 一、枚举类型定义

### quality_status_t — 数据质量状态
| 值 | 说明 |
|----|------|
| pending | 待验证 |
| valid | 已验证有效 |
| warning | 有警告但可用 |
| error | 数据异常 |
| deprecated | 已废弃 |

### trend_direction_t — 趋势方向
| 值 | 说明 |
|----|------|
| bullish | 偏多 |
| neutral | 中性 |
| bearish | 偏空 |

### scenario_type_t — 长期情景
| 值 | 说明 |
|----|------|
| bear | 熊市情景 |
| base | 基准情景 |
| bull | 牛市情景 |

### severity_level_t — 严重程度
| 值 | 说明 |
|----|------|
| low | 低 |
| medium | 中 |
| high | 高 |
| critical | 严重 |

### data_category_t — 数据分类
| 值 | 对应类别 |
|----|----------|
| gold | 1-黄金行情 |
| fed | 2-美联储与利率 |
| inflation | 3-通胀 |
| employment | 4-就业与经济 |
| usd | 5-美元 |
| treasury | 6-美债 |
| oil | 7-原油 |
| stock | 8-美股与风险 |
| gold_fund | 9-黄金资金面 |
| central_bank | 10-全球央行 |
| geopolitical | 11-地缘政治 |
| technical | 12-技术面 |
| precious_metals | 13-其他贵金属 |
| industrial_metals | 14-工业金属 |
| prediction | 预测 |
| report | 报告 |

---

## 二、数据表字典

### 2.1 data_sources — 数据源注册表

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | SERIAL | PK | 自增主键 |
| source_name | VARCHAR(100) | NOT NULL, UNIQUE | 数据源名称 |
| source_type | VARCHAR(50) | NOT NULL | 类型：api/web_scrape/manual/file |
| category | data_category_t | NOT NULL | 数据分类 |
| provider | VARCHAR(200) | | 提供方 |
| base_url | TEXT | | API 基础 URL |
| description | TEXT | | 描述 |
| is_active | BOOLEAN | DEFAULT TRUE | 是否启用 |
| config | JSONB | DEFAULT '{}' | 连接配置（不含密钥） |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

---

### 2.2 migration_versions — 迁移版本跟踪

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| version | VARCHAR(50) | PK | 版本号（如 V001） |
| description | TEXT | | 描述 |
| applied_at | TIMESTAMPTZ | DEFAULT NOW() | 执行时间 |

---

### 2.3 gold_prices — 黄金现货价格（类别1）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| price_type | VARCHAR(20) | NOT NULL, DEFAULT 'spot' | 定价类型：spot/lbma_am/lbma_pm |
| symbol | VARCHAR(20) | NOT NULL, DEFAULT 'XAUUSD' | 交易符号 |
| open | NUMERIC(12,4) | | 开盘价 |
| high | NUMERIC(12,4) | | 最高价 |
| low | NUMERIC(12,4) | | 最低价 |
| close | NUMERIC(12,4) | | 收盘价 |
| change_value | NUMERIC(12,4) | | 涨跌额 |
| change_pct | NUMERIC(8,4) | | 涨跌幅 % |
| volume | BIGINT | | 成交量 |
| open_interest | BIGINT | | 持仓量 |
| volatility | NUMERIC(8,4) | | 隐含波动率 % |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, price_type, symbol, source)`

---

### 2.4 gold_futures — 黄金期货价格（类别1）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| contract | VARCHAR(20) | NOT NULL | 合约月份（如 202412） |
| exchange | VARCHAR(20) | DEFAULT 'COMEX' | 交易所 |
| open | NUMERIC(12,4) | | 开盘价 |
| high | NUMERIC(12,4) | | 最高价 |
| low | NUMERIC(12,4) | | 最低价 |
| close | NUMERIC(12,4) | | 收盘价 |
| settle | NUMERIC(12,4) | | 结算价 |
| change_value | NUMERIC(12,4) | | 涨跌额 |
| change_pct | NUMERIC(8,4) | | 涨跌幅 % |
| volume | BIGINT | | 成交量 |
| open_interest | BIGINT | | 持仓量 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, contract, exchange, source)`

---

### 2.5 precious_metals — 其他贵金属（类别13）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| metal | VARCHAR(20) | NOT NULL | 金属：silver/platinum/palladium |
| symbol | VARCHAR(20) | NOT NULL | 符号：XAGUSD/XPTUSD/XPDUSD |
| open | NUMERIC(12,4) | | 开盘价 |
| high | NUMERIC(12,4) | | 最高价 |
| low | NUMERIC(12,4) | | 最低价 |
| close | NUMERIC(12,4) | | 收盘价 |
| change_value | NUMERIC(12,4) | | 涨跌额 |
| change_pct | NUMERIC(8,4) | | 涨跌幅 % |
| volume | BIGINT | | 成交量 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, metal, symbol, source)`

---

### 2.6 industrial_metals — 工业金属（类别14）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| metal | VARCHAR(20) | NOT NULL | 金属：copper/aluminum/zinc/nickel/lead/tin |
| symbol | VARCHAR(20) | NOT NULL | 交易符号 |
| exchange | VARCHAR(30) | | 交易所：LME/SHFE/COMEX |
| open | NUMERIC(12,4) | | 开盘价 |
| high | NUMERIC(12,4) | | 最高价 |
| low | NUMERIC(12,4) | | 最低价 |
| close | NUMERIC(12,4) | | 收盘价 |
| change_value | NUMERIC(12,4) | | 涨跌额 |
| change_pct | NUMERIC(8,4) | | 涨跌幅 % |
| volume | BIGINT | | 成交量 |
| inventory | NUMERIC(16,2) | | 库存量（吨） |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, metal, exchange, source)`

---

### 2.7 usd_data — 美元数据（类别5）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| pair | VARCHAR(20) | NOT NULL | 货币对：DXY/EURUSD/USDJPY/USDCNH/GBPUSD/AUDUSD |
| open | NUMERIC(12,6) | | 开盘价 |
| high | NUMERIC(12,6) | | 最高价 |
| low | NUMERIC(12,6) | | 最低价 |
| close | NUMERIC(12,6) | | 收盘价 |
| change_value | NUMERIC(12,6) | | 涨跌额 |
| change_pct | NUMERIC(8,4) | | 涨跌幅 % |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, pair, source)`

---

### 2.8 treasury_yields — 美债收益率（类别6）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| maturity | VARCHAR(10) | NOT NULL | 期限：3M/1Y/2Y/5Y/10Y/30Y |
| yield | NUMERIC(8,4) | | 名义收益率 % |
| real_yield | NUMERIC(8,4) | | 实际收益率 %（TIPS） |
| spread_to_10y | NUMERIC(8,4) | | 与 10Y 利差 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, maturity, source)`

---

### 2.9 oil_data — 原油数据（类别7）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| oil_type | VARCHAR(20) | NOT NULL | 类型：wti/brent/eia_inventory/opec_crude |
| open | NUMERIC(10,2) | | 开盘价 |
| high | NUMERIC(10,2) | | 最高价 |
| low | NUMERIC(10,2) | | 最低价 |
| close | NUMERIC(10,2) | | 收盘价 |
| change_value | NUMERIC(10,2) | | 涨跌额 |
| change_pct | NUMERIC(8,4) | | 涨跌幅 % |
| volume | BIGINT | | 成交量 |
| inventory_bbl | BIGINT | | 库存（桶），仅 eia_inventory |
| opec_production | NUMERIC(12,2) | | OPEC 产量（千桶/日），仅 opec_crude |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, oil_type, source)`

---

### 2.10 stock_market — 美股与风险（类别8）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| index_symbol | VARCHAR(20) | NOT NULL | 指数：SPX/NDX/DJI/VIX/GVZ |
| open | NUMERIC(14,4) | | 开盘价 |
| high | NUMERIC(14,4) | | 最高价 |
| low | NUMERIC(14,4) | | 最低价 |
| close | NUMERIC(14,4) | | 收盘价 |
| change_value | NUMERIC(14,4) | | 涨跌额 |
| change_pct | NUMERIC(8,4) | | 涨跌幅 % |
| volume | BIGINT | | 成交量 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, index_symbol, source)`

---

### 2.11 fed_events — 美联储与利率事件（类别2）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| event_date | TIMESTAMPTZ | NOT NULL | 事件日期 |
| event_type | VARCHAR(50) | NOT NULL | 类型：fomc_meeting/rate_decision/dot_plot/policy_statement/speech |
| fed_funds_rate | NUMERIC(6,4) | | 联邦基金利率 % |
| target_range_low | NUMERIC(6,4) | | 目标区间下限 |
| target_range_high | NUMERIC(6,4) | | 目标区间上限 |
| dot_plot_median | NUMERIC(6,4) | | 点阵图中位数 |
| title | VARCHAR(300) | | 标题 |
| summary | TEXT | | 摘要 |
| full_text | TEXT | | 全文 |
| impact_level | severity_level_t | | 影响程度 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

---

### 2.12 economic_indicators — 经济指标（类别3+4）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| indicator_type | VARCHAR(50) | NOT NULL | 指标：cpi/core_cpi/pce/ppi/inflation_expectation/nonfarm/unemployment/gdp/pmi/retail_sales |
| period | VARCHAR(20) | | 数据周期（2024-01/2024Q1） |
| actual_value | NUMERIC(14,4) | | 实际公布值 |
| revised_value | NUMERIC(14,4) | | 修正值 |
| consensus | NUMERIC(14,4) | | 市场预期值 |
| previous_value | NUMERIC(14,4) | | 前值 |
| unit | VARCHAR(20) | | 单位（%/千人/十亿美元） |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, indicator_type, period, source)`

---

### 2.13 gold_etf_flows — 黄金 ETF 资金流（类别9）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| etf_name | VARCHAR(50) | NOT NULL | ETF 名称：GLD/IAU 等 |
| flow_tons | NUMERIC(14,4) | | 当日流入/流出（吨），正=流入 |
| flow_usd | NUMERIC(16,2) | | 当日流入/流出（美元） |
| total_holdings_tons | NUMERIC(16,4) | | 总持仓（吨） |
| total_holdings_usd | NUMERIC(18,2) | | 总持仓（美元） |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, etf_name, source)`

---

### 2.14 cftc_positions — CFTC 持仓（类别9）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 报告截止日期（每周五） |
| report_type | VARCHAR(50) | DEFAULT 'gold' | 报告类型 |
| managed_money_long | BIGINT | | 管理资金多头 |
| managed_money_short | BIGINT | | 管理资金空头 |
| managed_money_net | BIGINT | | 管理资金净持仓 |
| total_long | BIGINT | | 总多头 |
| total_short | BIGINT | | 总空头 |
| total_net | BIGINT | | 总净持仓 |
| change_long | BIGINT | | 多头变化 |
| change_short | BIGINT | | 空头变化 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, report_type, source)`

---

### 2.15 central_bank_reserves — 央行黄金储备（类别10）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| country | VARCHAR(100) | NOT NULL | 国家 |
| bank_name | VARCHAR(200) | | 央行名称 |
| action | VARCHAR(20) | NOT NULL | 操作：purchase/sale/hold |
| volume_tons | NUMERIC(14,4) | | 交易/变化量（吨） |
| total_reserves_tons | NUMERIC(16,4) | | 总储备（吨） |
| reserves_pct | NUMERIC(6,2) | | 黄金占外储比例 % |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, country, source)`

---

### 2.16 technical_indicators — 技术指标（类别12）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 数据时间戳 |
| symbol | VARCHAR(20) | NOT NULL | 交易符号：XAUUSD/XAGUSD 等 |
| indicator_name | VARCHAR(30) | NOT NULL | 指标：sma/ema/rsi/macd/macd_signal/macd_hist/bollinger_upper/bollinger_mid/bollinger_lower/adx/fibonacci_level |
| period | INTEGER | | 计算周期（14/20/50/200） |
| category | indicator_category_t | | 类别：trend/momentum/volatility/volume/support_resistance |
| value | NUMERIC(14,6) | | 指标值 |
| extra_data | JSONB | DEFAULT '{}' | 附加参数 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

**唯一约束**：`(timestamp, symbol, indicator_name, period, source)`

---

### 2.17 geopolitical_events — 地缘政治事件（类别11）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| event_date | TIMESTAMPTZ | NOT NULL | 事件日期 |
| event_type | VARCHAR(50) | NOT NULL | 类型：war/conflict/sanction/financial_risk/election/trade_dispute |
| title | VARCHAR(500) | NOT NULL | 标题 |
| description | TEXT | | 描述 |
| region | VARCHAR(100) | | 地区 |
| countries | TEXT[] | | 涉及国家列表 |
| severity | severity_level_t | | 严重程度 |
| gold_impact | VARCHAR(20) | | 对黄金影响：bullish/bearish/neutral |
| gold_impact_detail | TEXT | | 影响分析详情 |
| status | VARCHAR(20) | DEFAULT 'ongoing' | 状态：ongoing/resolved/escalated |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

---

### 2.18 predictions_short_term — 短期预测（1小时～5天）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| generated_at | TIMESTAMPTZ | NOT NULL | 生成时间 |
| symbol | VARCHAR(20) | NOT NULL, DEFAULT 'XAUUSD' | 预测标的 |
| trend | trend_direction_t | | 趋势方向 |
| probability_up | NUMERIC(6,4) | | 上涨概率 |
| probability_down | NUMERIC(6,4) | | 下跌概率 |
| probability_sideways | NUMERIC(6,4) | | 震荡概率 |
| confidence | NUMERIC(6,4) | | 置信度 |
| support_levels | JSONB | | 支撑位 S1-S5（含依据） |
| resistance_levels | JSONB | | 阻力位 R1-R5（含依据） |
| bullish_factors | JSONB | | 利多因素 |
| bearish_factors | JSONB | | 利空因素 |
| invalidation_condition | TEXT | | 预测失效条件 |
| agent_name | VARCHAR(100) | | 生成 Agent |
| model_version | VARCHAR(50) | | 模型版本 |
| input_data_version | VARCHAR(100) | | 输入数据版本 |
| metadata | JSONB | DEFAULT '{}' | 附加元数据 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

---

### 2.19 predictions_long_term — 长期预测（1～12个月）

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| generated_at | TIMESTAMPTZ | NOT NULL | 生成时间 |
| symbol | VARCHAR(20) | NOT NULL, DEFAULT 'XAUUSD' | 预测标的 |
| scenario | scenario_type_t | NOT NULL | 情景：bear/base/bull |
| probability | NUMERIC(6,4) | | 情景概率 |
| target_price_low | NUMERIC(12,4) | | 目标价下限 |
| target_price_high | NUMERIC(12,4) | | 目标价上限 |
| target_price_mid | NUMERIC(12,4) | | 目标价中位 |
| core_drivers | JSONB | | 核心驱动因素 |
| risks | JSONB | | 风险因素 |
| time_horizon_months | INTEGER | | 预测跨度（月） |
| agent_name | VARCHAR(100) | | 生成 Agent |
| model_version | VARCHAR(50) | | 模型版本 |
| input_data_version | VARCHAR(100) | | 输入数据版本 |
| metadata | JSONB | DEFAULT '{}' | 附加元数据 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

---

### 2.20 ai_reports — AI 研究报告

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| report_date | TIMESTAMPTZ | NOT NULL | 报告日期 |
| report_type | report_type_t | NOT NULL | 类型：daily/weekly/monthly/special/ai_analysis |
| title | VARCHAR(500) | NOT NULL | 标题 |
| summary | TEXT | | 摘要 |
| content | TEXT | | 报告全文（Markdown） |
| data_facts | JSONB | | 数据事实部分 |
| model_outputs | JSONB | | 模型输出部分 |
| ai_inferences | JSONB | | AI 推断部分 |
| uncertainties | JSONB | | 不确定性说明 |
| conclusions | JSONB | | 结论 |
| agent_name | VARCHAR(100) | | 生成 Agent |
| model_version | VARCHAR(50) | | 模型版本 |
| input_data_version | VARCHAR(100) | | 输入数据版本 |
| prediction_ids | BIGINT[] | | 关联预测 ID 列表 |
| metadata | JSONB | DEFAULT '{}' | 附加元数据 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

---

### 2.21 data_quality_logs — 数据质量日志

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| timestamp | TIMESTAMPTZ | NOT NULL | 检测时间 |
| table_name | VARCHAR(100) | NOT NULL | 关联表名 |
| record_id | BIGINT | | 关联记录 ID |
| check_type | VARCHAR(50) | NOT NULL | 检查类型：completeness/accuracy/timeliness/consistency/validity |
| severity | severity_level_t | NOT NULL | 严重程度 |
| message | TEXT | NOT NULL | 问题描述 |
| details | JSONB | DEFAULT '{}' | 详细信息 |
| resolved | BOOLEAN | DEFAULT FALSE | 是否已解决 |
| resolved_at | TIMESTAMPTZ | | 解决时间 |
| source | VARCHAR(100) | NOT NULL | 数据来源 |
| collected_at | TIMESTAMPTZ | DEFAULT NOW() | 采集时间 |
| quality_status | quality_status_t | DEFAULT 'pending' | 质量状态 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |

---

### 2.22 data_snapshot_versions — 数据快照版本

| 列名 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | BIGSERIAL | PK | 自增主键 |
| snapshot_date | DATE | NOT NULL | 快照日期 |
| version_tag | VARCHAR(100) | NOT NULL, UNIQUE | 版本标签（如 v20240822） |
| description | TEXT | | 描述 |
| table_counts | JSONB | | 各表记录数 |
| data_summary | JSONB | | 数据摘要统计 |
| is_valid | BOOLEAN | DEFAULT TRUE | 是否有效 |
| created_at | TIMESTAMPTZ | DEFAULT NOW() | 创建时间 |
| updated_at | TIMESTAMPTZ | DEFAULT NOW() | 更新时间 |
