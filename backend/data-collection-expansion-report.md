# GoldSight AI V3.0 - 数据采集扩展自检报告

> 执行时间：2026-08-22  
> 执行角色：Data Agent 第二阶段（数据采集扩展 Agent）

---

## 一、任务完成概览

| 任务项 | 状态 | 说明 |
|--------|------|------|
| 现有 3 个采集器扩展到 90+ 天 | ✅ 完成 | 黄金 120 条、美元 90 条、美债 240 条 |
| 新增 5 个数据源采集器 | ✅ 完成 | 2Y 国债、原油、S&P500、CPI、VIX |
| 技术指标重新计算 | ✅ 完成 | 18 种指标全部可计算，共 1784 条 |
| API 端点扩展 | ✅ 完成 | 新增 5 个数据查询端点 + 统计端点 |

---

## 二、采集器清单（8 个）

### 原有采集器（已扩展）

| 采集器 | 数据源 | 目标表 | 默认天数 | 入库条数 |
|--------|--------|--------|----------|----------|
| GoldPriceCollector | NBP + Frankfurter | gold_prices | 120 | 120 |
| UsdDataCollector | Frankfurter/ECB | usd_data | 120 | 90 |
| TreasuryYieldCollector | FRED (DGS10) | treasury_yields | 120 | 120 |

### 新增采集器

| 采集器 | 数据源 | 目标表 | 默认天数 | 入库条数 |
|--------|--------|--------|----------|----------|
| TreasuryYield2YCollector | FRED (DGS2) | treasury_yields | 120 | 120 |
| OilPriceCollector | FRED (DCOILWTICO) | oil_data | 120 | 120 |
| StockMarketCollector | FRED (SP500) | stock_market | 120 | 120 |
| EconomicIndicatorCollector | FRED (CPIAUCSL) | economic_indicators | 36 月 | 36 |
| VixCollector | FRED (VIXCLS) | stock_market | 120 | 120 |

---

## 三、数据库各表数据量

| 表名 | 记录数 | 说明 |
|------|--------|------|
| gold_prices | 120 条 | 黄金价格，2026-03-04 ~ 2026-08-21 |
| usd_data | 90 条 | EUR/USD 汇率 |
| treasury_yields | 240 条 | 10Y（120 条）+ 2Y（120 条）|
| oil_data | 120 条 | WTI 原油价格 |
| stock_market | 240 条 | S&P 500（120 条）+ VIX（120 条）|
| precious_metals | 0 条 | 暂无（NBP 无白银 API）|
| economic_indicators | 36 条 | 美国 CPI 月度数据（3 年）|
| technical_indicators | 1784 条 | 18 种技术指标 |
| **总计** | **2630 条** | |

---

## 四、技术指标计算能力（核心突破）

### 之前（5 条数据）
- 仅能计算：MA5（5 条）
- 无法计算：MA10、MA20、MA60、RSI、MACD、布林带等

### 现在（120 条数据）

| 指标名称 | 周期 | 类别 | 可计算记录数 | 最小数据要求 |
|----------|------|------|-------------|-------------|
| SMA | 5 | 趋势 | 116 条 | 5 |
| SMA | 10 | 趋势 | 111 条 | 10 |
| SMA | 20 | 趋势 | 101 条 | 20 |
| **SMA** | **60** | **趋势** | **61 条** | **60** ✅ |
| EMA | 12 | 趋势 | 109 条 | 12 |
| EMA | 26 | 趋势 | 95 条 | 26 |
| MACD | 12 | 趋势 | 95 条 | 26 |
| MACD Signal | 26 | 趋势 | 87 条 | 26 |
| MACD Hist | 9 | 趋势 | 87 条 | 26 |
| ADX | 14 | 趋势 | 91 条 | 30 |
| RSI | 14 | 动量 | 106 条 | 15 |
| Stochastic %K | 14 | 动量 | 105 条 | 16 |
| Stochastic %D | 14 | 动量 | 105 条 | 16 |
| ROC | 14 | 动量 | 106 条 | 15 |
| Bollinger Upper | 20 | 波动 | 101 条 | 20 |
| Bollinger Mid | 20 | 波动 | 101 条 | 20 |
| Bollinger Lower | 20 | 波动 | 101 条 | 20 |
| ATR | 14 | 波动 | 106 条 | 15 |

**关键突破：MA60 现在可以计算（61 条记录），满足了任务核心需求！**

---

## 五、API 端点清单

### 新增查询端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/data/oil` | GET | 查询原油价格数据 |
| `/api/v1/data/stock-market` | GET | 查询美股/指数数据 |
| `/api/v1/data/precious-metals` | GET | 查询贵金属数据 |
| `/api/v1/data/economic` | GET | 查询经济指标数据 |
| `/api/v1/data/stats` | GET | 各表数据统计概览 |

### 已有端点

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/v1/data/gold-prices` | GET | 查询黄金价格数据 |
| `/api/v1/data/usd` | GET | 查询美元数据 |
| `/api/v1/data/treasury-yields` | GET | 查询国债收益率 |
| `/api/v1/data/collectors` | GET | 列出已注册采集器 |
| `/api/v1/data/collect/{name}` | POST | 手动触发采集 |
| `/api/v1/indicators/calculate` | POST | 触发指标计算 |
| `/api/v1/indicators` | GET | 查询技术指标 |

---

## 六、数据源说明

### 使用的免费数据源

| 数据源 | 提供方 | 特点 | 用于 |
|--------|--------|------|------|
| NBP API | 波兰国家银行 | 免费、无需 Key、国内可达 | 黄金价格 |
| Frankfurter | 欧洲央行 ECB | 免费、无需 Key、国内可达 | EUR/USD 汇率 |
| FRED CSV | 美联储 | 免费、无需 Key、数据丰富 | 国债、原油、股指、CPI、VIX |

### 未使用 Yahoo Finance 的原因
按要求约束，Yahoo Finance 在国内不可用，全部使用上述替代数据源。

### 白银数据源说明
NBP API 不提供白银价格端点（返回 404），Stooq 同样不可用。
因此将第 5 个新采集器调整为 **2 年期国债收益率**（FRED DGS2），
该数据对收益率曲线分析和黄金预测具有重要价值。

---

## 七、代码变更清单

### 新增文件（5 个采集器）
- `backend/app/services/data_collection/collectors/treasury_yield_2y_collector.py`
- `backend/app/services/data_collection/collectors/oil_price_collector.py`
- `backend/app/services/data_collection/collectors/stock_market_collector.py`
- `backend/app/services/data_collection/collectors/economic_indicator_collector.py`
- `backend/app/services/data_collection/collectors/vix_collector.py`

### 修改文件
- `backend/app/services/data_collection/collectors/gold_price_collector.py` — days 默认 5→120
- `backend/app/services/data_collection/collectors/usd_data_collector.py` — days 默认 5→120
- `backend/app/services/data_collection/collectors/treasury_yield_collector.py` — days 默认 10→120
- `backend/app/services/data_collection/collectors/__init__.py` — 注册新采集器
- `backend/app/services/data_collection/__init__.py` — 注册新采集器
- `backend/app/services/data_collection/runner.py` — period→days 参数修正
- `backend/app/api/v1/data.py` — 新增 5 个查询端点 + 统计端点

---

## 八、运行命令参考

```bash
# 运行所有采集器（默认 120 天）
cd backend
..\.venv\Scripts\python.exe -m app.services.data_collection.runner --all

# 运行指定采集器
..\.venv\Scripts\python.exe -m app.services.data_collection.runner --collector GoldPriceCollector --days 90

# 列出所有采集器
..\.venv\Scripts\python.exe -m app.services.data_collection.runner --list

# 启动后端服务
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload
```

---

## 九、结论

1. **数据量扩展**：从原来仅 5 条黄金数据扩展到 120 条，满足 MA60 等长期指标的计算需求
2. **数据源扩展**：从 3 个数据源扩展到 8 个，覆盖黄金、美元、美债（2Y+10Y）、原油、美股、CPI、VIX
3. **技术指标突破**：从仅能计算 MA5 扩展到 18 种指标全部可计算，共产生 1784 条指标记录
4. **数据库总量**：8 张业务表共 2630 条记录
5. **框架遵循**：所有新采集器严格遵循开闭原则，自动注册，无需修改框架代码
