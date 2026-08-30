# GoldSight AI V3.0 - 技术指标计算模块自检报告

> 版本：V1.0 | 日期：2026-08-22 | 维护人：Technical Agent

---

## 一、交付物清单

| 编号 | 文件 | 说明 | 状态 |
|------|------|------|------|
| 1 | `backend/app/services/technical_analysis/__init__.py` | 技术分析模块初始化 | OK |
| 2 | `backend/app/services/technical_analysis/calculations.py` | 13 种技术指标计算函数 | OK |
| 3 | `backend/app/services/technical_analysis/engine.py` | 计算引擎（获取/计算/存储） | OK |
| 4 | `backend/app/api/v1/indicators.py` | 指标 API 端点 | OK |
| 5 | `backend/app/api/router.py` | 路由注册（已更新） | OK |
| 6 | `backend/tests/test_technical_indicators.py` | 25 个测试用例 | OK |

---

## 二、指标计算正确性验证

### 2.1 MA5 手动验证

**输入数据（gold_prices 表 5 条记录）：**

| 日期 | 收盘价 |
|------|--------|
| 2026-08-17 | 4404.4286 |
| 2026-08-18 | 4431.5434 |
| 2026-08-19 | 4450.2957 |
| 2026-08-20 | 4412.0309 |
| 2026-08-21 | 4497.2610 |

**手动计算：**
- MA5 = (4404.4286 + 4431.5434 + 4450.2957 + 4412.0309 + 4497.2610) / 5
- MA5 = 22195.5596 / 5 = **4439.11192**

**数据库存储值：** 4439.111920

**结论：完全匹配**

### 2.2 单元测试验证

| 指标 | 测试用例 | 验证方式 | 结果 |
|------|----------|----------|------|
| MA | test_ma5_basic | 已知 5 值平均 = 102.0 | PASSED |
| MA | test_ma_insufficient_data | 3 值 < period=5 → None | PASSED |
| MA | test_ma_with_more_data | 7 值取最后 5 个 | PASSED |
| EMA | test_ema_basic | 15 个递增价格，结果在合理范围 | PASSED |
| EMA | test_ema_equals_sma_for_exact_period | period=5 时 EMA=SMA=104.0 | PASSED |
| EMA | test_ema_insufficient_data | 2 值 < period=12 → None | PASSED |
| MACD | test_macd_insufficient_data | 20 值 < 26 → None | PASSED |
| MACD | test_macd_with_enough_data | 40 值，含 macd/signal/hist | PASSED |
| ADX | test_adx_insufficient_data | 20 值 < 30 → None | PASSED |
| RSI | test_rsi_basic | 全部上涨 → RSI=100 | PASSED |
| RSI | test_rsi_all_decline | 全部下跌 → RSI=0 | PASSED |
| RSI | test_rsi_insufficient_data | 3 值 < 15 → None | PASSED |
| Stochastic | test_stochastic_insufficient_data | 10 值 < 16 → None | PASSED |
| Stochastic | test_stochastic_basic | 18 值，%K/%D 在 0-100 范围 | PASSED |
| ROC | test_roc_basic | (115-100)/100*100 = 15.0 | PASSED |
| ROC | test_roc_insufficient_data | 3 值 < 15 → None | PASSED |
| Bollinger | test_bollinger_basic | upper > middle > lower | PASSED |
| Bollinger | test_bollinger_insufficient_data | 3 值 < 20 → None | PASSED |
| ATR | test_atr_basic | 20 值，ATR > 0 | PASSED |
| ATR | test_atr_insufficient_data | 10 值 < 15 → None | PASSED |

---

## 三、数据库写入验证

### 3.1 technical_indicators 表数据

```
 id | timestamp            | symbol | indicator_name | period | category | value       | source           | quality_status
----+----------------------+------+----------------+--------+----------+-------------+------------------+----------------
  1 | 2026-08-21 00:00:00+00| XAUUSD | sma            |      5 | trend    | 4439.111920 | technical_engine | valid
```

**验证结论：**
- 数据成功写入 technical_indicators 表
- 时间戳对应第 5 条价格数据（MA5 可计算的最早时间点）
- source 标记为 'technical_engine'，可追溯
- quality_status 为 'valid'

### 3.2 幂等写入验证

引擎使用 `ON CONFLICT DO UPDATE` 实现幂等写入，重复执行不会产生重复记录。

---

## 四、API 端点验证

### 4.1 POST /api/v1/indicators/calculate

**请求：** `POST /api/v1/indicators/calculate?symbol=XAUUSD`

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "status": "success",
    "symbol": "XAUUSD",
    "price_data_points": 5,
    "total_records": 1,
    "stored_records": 1,
    "indicators_summary": {
      "sma(5)": 1
    }
  }
}
```

### 4.2 GET /api/v1/indicators

**请求：** `GET /api/v1/indicators?symbol=XAUUSD`

**响应：**
```json
{
  "code": 200,
  "message": "success",
  "data": {
    "records": [
      {
        "id": 1,
        "timestamp": "2026-08-21T00:00:00+00:00",
        "symbol": "XAUUSD",
        "indicator_name": "sma",
        "period": 5,
        "category": "trend",
        "value": 4439.11192,
        "extra_data": {},
        "source": "technical_engine",
        "collected_at": "2026-08-22T08:39:52.224423+00:00",
        "quality_status": "valid"
      }
    ],
    "total": 1,
    "limit": 100,
    "offset": 0
  }
}
```

### 4.3 带过滤条件查询

**请求：** `GET /api/v1/indicators?indicator=sma&category=trend`

**结果：** 正确过滤，返回 1 条 SMA 记录。

---

## 五、数据不足处理

### 5.1 当前 5 条数据下的指标计算情况

| 指标 | 最小数据需求 | 5 条数据是否可计算 | 处理方式 |
|------|-------------|-------------------|----------|
| MA5 | 5 | 是 | 正常计算 |
| MA10 | 10 | 否 | 静默跳过 |
| MA20 | 20 | 否 | 静默跳过 |
| MA60 | 60 | 否 | 静默跳过 |
| EMA12 | 12 | 否 | 静默跳过 |
| EMA26 | 26 | 否 | 静默跳过 |
| MACD | 26 | 否 | 静默跳过 |
| ADX | 30 | 否 | 静默跳过 |
| RSI14 | 15 | 否 | 静默跳过 |
| Stochastic | 16 | 否 | 静默跳过 |
| ROC14 | 15 | 否 | 静默跳过 |
| Bollinger | 20 | 否 | 静默跳过 |
| ATR14 | 15 | 否 | 静默跳过 |

### 5.2 优雅降级机制

- 每个指标配置了 `min_data` 最小数据量阈值
- 数据不足时，`compute_all_indicators()` 直接跳过该指标
- 不产生错误日志，不抛出异常
- 随着新数据接入，更多指标会自动变得可计算

---

## 六、测试汇总

### 6.1 全量测试结果

```
43 passed, 3 skipped in 0.36s
```

- **43 通过**：所有计算函数测试 + 引擎逻辑测试 + 原有测试
- **3 跳过**：Windows 事件循环关闭导致的 async DB 测试跳过（已知限制）
- **0 失败**

### 6.2 测试覆盖范围

| 类别 | 测试数量 | 说明 |
|------|---------|------|
| MA 计算 | 3 | 基本计算、数据不足、多余数据 |
| EMA 计算 | 3 | 基本计算、SMA 等价性、数据不足 |
| MACD 计算 | 2 | 数据不足、正常计算 |
| ADX 计算 | 1 | 数据不足 |
| RSI 计算 | 3 | 全涨/全跌/数据不足 |
| Stochastic | 2 | 数据不足、正常计算 |
| ROC 计算 | 2 | 基本计算、数据不足 |
| Bollinger | 2 | 基本计算、数据不足 |
| ATR 计算 | 2 | 基本计算、数据不足 |
| 引擎逻辑 | 2 | 5 点数据模拟、早期时间点 |
| API 端点 | 3 | 查询/过滤/触发计算 |

---

## 七、架构设计说明

### 7.1 模块结构

```
backend/app/services/technical_analysis/
    __init__.py          # 模块导出
    calculations.py      # 13 种指标计算函数（纯 Python + numpy）
    engine.py            # 计算引擎（数据获取→计算→存储）

backend/app/api/v1/
    indicators.py        # 指标 API 端点
```

### 7.2 设计亮点

1. **纯 Python + numpy**：不依赖 TA-Lib，无需 C 编译器
2. **指标配置化**：通过 `INDICATOR_CONFIG` 列表管理，新增指标只需添加配置
3. **幂等写入**：`ON CONFLICT DO UPDATE` 支持增量更新
4. **优雅降级**：数据不足时静默跳过，不报错
5. **来源可追溯**：source='technical_engine'，与采集数据区分

### 7.3 增量更新支持

引擎对每个时间点使用截至该点的全部历史数据计算指标。重复执行时，`ON CONFLICT DO UPDATE` 确保已有记录被更新而非重复插入。新数据接入后重新运行即可获得更多指标值。

---

## 八、后续扩展建议

1. **数据量增长后**：MA10/MA20/MA60、EMA、MACD、RSI、Bollinger 等指标将自动可计算
2. **新增指标**：在 `INDICATOR_CONFIG` 中添加配置项即可，无需修改引擎代码
3. **自动触发**：可在 `DataPipeline.run()` 完成后调用 `run_calculation()` 实现采集后自动计算
4. **性能优化**：数据量超过 1000 条后，可考虑分批计算 + 缓存最近数据
