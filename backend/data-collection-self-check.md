# GoldSight AI V3.0 - 数据采集模块自检报告

**Data Agent 交付日期**：2026-08-22  
**模块位置**：`backend/app/services/data_collection/`

---

## 一、交付物清单

| 交付物 | 状态 | 说明 |
|--------|------|------|
| 通用数据采集框架 | ✅ 完成 | BaseCollector + CollectorRegistry + DataPipeline |
| 黄金价格采集器 | ✅ 完成 | NBP + Frankfurter 数据源 |
| 美元数据采集器 | ✅ 完成 | Frankfurter/ECB 数据源 |
| 国债收益率采集器 | ✅ 完成 | FRED 数据源 |
| 数据写入 PostgreSQL | ✅ 验证通过 | 3 张表共写入 23 条真实数据 |
| 查询 API 端点 | ✅ 完成 | 5 个端点（3 查询 + 1 列表 + 1 触发） |
| 基础测试 | ✅ 通过 | 20 passed, 1 skipped |
| requirements.txt | ✅ 已更新 | 新增 yfinance, pandas 等依赖 |

---

## 二、自检结果

### 2.1 采集器是否能拉到真实数据

| 采集器 | 数据源 | 结果 | 样本数据 |
|--------|--------|------|----------|
| GoldPriceCollector | NBP（波兰央行）+ Frankfurter | ✅ 成功获取 5 天数据 | 2026-08-21: $4497.26/盎司 |
| UsdDataCollector | Frankfurter（欧洲央行） | ✅ 成功获取 8 天数据 | 2026-08-21: EUR/USD 1.1699 |
| TreasuryYieldCollector | FRED（美联储） | ✅ 成功获取 10 天数据 | 2026-08-20: 10Y 4.69% |

> **说明**：原计划使用 Yahoo Finance，但因国内网络环境不可达，已替换为三个可访问的公开数据源。框架设计为数据源可替换，后续网络条件允许时可无缝切换。

### 2.2 数据是否成功写入 PostgreSQL

| 表名 | 写入记录数 | 验证 SQL |
|------|-----------|----------|
| gold_prices | 5 条 | `SELECT count(*) FROM gold_prices` → 5 |
| usd_data | 8 条 | `SELECT count(*) FROM usd_data` → 8 |
| treasury_yields | 10 条 | `SELECT count(*) FROM treasury_yields` → 10 |

所有记录均包含 `source`（数据来源）和 `collected_at`（采集时间）字段。

### 2.3 查询 API 是否返回正确数据

| 端点 | 方法 | 测试结果 |
|------|------|----------|
| `GET /api/v1/data/gold-prices` | 查询黄金价格 | ✅ 200，返回 records + total |
| `GET /api/v1/data/usd` | 查询美元数据 | ✅ 200，返回 records + total |
| `GET /api/v1/data/treasury-yields` | 查询国债收益率 | ✅ 200，返回 records + total |
| `GET /api/v1/data/collectors` | 列出采集器 | ✅ 200，返回 3 个采集器信息 |
| `POST /api/v1/data/collect/{name}` | 手动触发采集 | ✅ 可用 |

所有端点均支持 `start_date`、`end_date`、`limit`、`offset`、`source` 查询参数。

### 2.4 错误处理和重试是否正常工作

- **重试机制**：UsdDataCollector 开发过程中发现 URL 拼接错误，流水线自动重试 3 次（指数退避），日志清晰记录每次重试。
- **未注册采集器**：流水线返回 `status: "error"`，`message: "采集器未注册"`，不抛异常。
- **数据验证**：各采集器的 `validate()` 方法正确过滤非法记录（空值、负价格、超范围收益率）。
- **ON CONFLICT DO NOTHING**：重复运行采集器不会插入重复数据。

### 2.5 测试结果

```
20 passed, 1 skipped in 0.45s
```

- 11 个数据采集相关测试全部通过
- 5 个原有测试（config + health）不受影响
- 1 个测试因 Windows asyncpg 事件循环限制被跳过（非代码问题）

---

## 三、框架架构

```
backend/app/services/data_collection/
├── __init__.py              # 模块入口，导出核心组件
├── base_collector.py        # 采集器抽象基类
├── registry.py              # 采集器注册中心（单例，开闭原则）
├── pipeline.py              # 数据流水线（获取→清洗→验证→入库）
├── runner.py                # 命令行运行脚本
└── collectors/
    ├── __init__.py
    ├── gold_price_collector.py      # NBP + Frankfurter → gold_prices
    ├── usd_data_collector.py        # Frankfurter/ECB → usd_data
    └── treasury_yield_collector.py  # FRED → treasury_yields
```

**核心设计原则**：
1. **开闭原则**：新增数据源只需继承 `BaseCollector` 并放入 `collectors/` 目录，无需修改框架代码
2. **数据源可替换**：采集器与具体供应商解耦，`source_name` 属性标识来源
3. **统一接口**：`fetch() → clean() → validate() → store()` 标准流水线
4. **自动元数据**：框架自动填充 `source`、`collected_at`、`quality_status`

---

## 四、已知限制与后续改进

1. **黄金价格精度**：当前通过 NBP（PLN/克）+ 汇率换算得到 USD/盎司近似值，与直接报价可能有微小偏差。后续接入 Yahoo Finance 或 LBMA 可获取更精确数据。
2. **DXY 代理**：当前使用 EUR/USD 汇率作为美元数据代理，非严格意义上的美元指数。后续可接入 ICE 或 Yahoo Finance 获取真实 DXY。
3. **Windows 测试限制**：asyncpg 在 Windows + Python 3.9 测试环境中存在事件循环管理问题，导致个别 API 测试需跳过。
4. **定时调度**：当前需手动运行采集器，后续可集成 APScheduler 实现定时自动采集。

---

## 五、运行方式

```bash
# 在 backend/ 目录下执行

# 列出已注册采集器
.venv\Scripts\python.exe -m app.services.data_collection.runner --list

# 运行所有采集器
.venv\Scripts\python.exe -m app.services.data_collection.runner --all

# 运行指定采集器
.venv\Scripts\python.exe -m app.services.data_collection.runner --collector GoldPriceCollector

# 通过 API 手动触发
curl -X POST http://localhost:8000/api/v1/data/collect/GoldPriceCollector
```
