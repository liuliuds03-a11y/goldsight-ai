# GoldSight AI V3.0 — 项目全局开发指南

> 本文档是 GoldSight 项目的**总入口文档**。任何新加入的开发 Agent，无论负责哪个模块，都必须先阅读本文档，了解项目全貌后再开始工作。
>
> 最后更新：2026-08-21 | 维护人：PM Agent

---

## 一、项目是什么？

**GoldSight AI** 是一个以**黄金为核心**的全球多金属智能监测、分析与预测平台。

核心价值：把分散在全球各市场的黄金相关数据（行情、宏观经济、利率、美元、美债、原油、美股、ETF、CFTC、央行购金、地缘政治、新闻等）**自动汇总、清洗、分析、解释**，形成可理解的研究结论和预测。

系统不是简单展示行情，而是：
1. 持续采集多源数据 → 2. 指标计算 → 3. 多个专业 Agent 并行分析 → 4. 量化模型 → 5. DeepSeek 大模型综合 → 6. 决策融合 → 7. 输出预测报告

**重要声明：GoldSight 是研究与分析系统，预测具有概率性，不构成投资建议。**

---

## 二、技术栈总览

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 后端 | Python 3.9+ / FastAPI | 数据处理、API 服务、Agent 编排 |
| 前端 | TypeScript / React 18 / Vite | 金融 Dashboard、图表展示 |
| 图表 | ECharts | K 线、指标、趋势等金融图表 |
| 数据库 | PostgreSQL 16 | 结构化金融数据持久化 |
| 缓存 | Redis 7 | 缓存、任务队列 |
| 容器 | Docker + Docker Compose | 本地开发环境统一 |
| AI | DeepSeek API | 综合分析、报告生成 |
| 版本控制 | Git | 代码管理 |

---

## 三、项目目录结构

```
GoldSight Multi-Metal/
├── backend/          # 后端代码（Backend Agent 负责）
├── frontend/         # 前端代码（Frontend Agent 负责）
├── database/         # 数据库代码（Database Agent 负责）
├── docs/             # 项目文档（PM + 各 Agent 共同维护）
│   ├── environment/  # 环境报告
│   ├── architecture/ # 架构设计
│   ├── api/          # API 规范
│   ├── data/         # 数据文档
│   └── development/  # 开发规范
├── docker-compose.yml    # Docker 容器编排
├── .env                  # 环境变量（不提交 Git）
├── .env.example          # 环境变量模板
└── .gitignore            # Git 忽略规则
```

**关键原则：每个 Agent 只负责自己的目录，不跨目录修改。需要跨模块时先向 PM 报告。**

---

## 四、开发阶段与推进顺序

项目分为 12 个阶段，**严格按顺序推进**，每个阶段完成并经 PM 验收后才进入下一阶段：

| 阶段 | 名称 | 主要工作 | 负责 Agent | 当前状态 |
|------|------|----------|------------|----------|
| 0 | 环境检查与配置 | 确认开发环境、安装依赖 | 环境配置 Agent | **当前阶段** |
| 1 | 总体方案确认 | 数据需求、技术方案设计 | PM + 各 Agent | 未开始 |
| 2 | 数据库基础 | Schema 设计、Migration | Database Agent | 未开始 |
| 3 | 数据采集与质量 | 数据源接入、采集调度 | Data Agent | 未开始 |
| 4 | 指标与专业分析 | 技术/宏观/市场/资金/地缘 Agent | 各分析 Agent | 未开始 |
| 5 | Quant 与回测 | 特征工程、量化模型、回测 | Quant Agent | 未开始 |
| 6 | DeepSeek 集成 | AI 综合分析、报告生成 | DeepSeek Agent | 未开始 |
| 7 | Decision 融合 | 多 Agent 结论融合、最终判断 | Decision Agent | 未开始 |
| 8 | Backend API | 完整 API 服务 | Backend Agent | 未开始 |
| 9 | Frontend | Dashboard、页面、图表 | Frontend Agent | 未开始 |
| 10 | 全面测试 | 单元/集成/API/性能测试 | QA Agent | 未开始 |
| 11 | 部署 | 服务器部署、正式运行 | 部署 Agent | 未开始 |

---

## 五、Agent 分工与职责

本项目采用**多 Agent 协作模式**，每个 Agent 有明确的责任边界：

### 5.1 环境配置 Agent
- **职责**：检查并配置开发环境（Python、Node.js、Docker、PostgreSQL、Redis 等）
- **交付物**：环境检查报告、安装配置记录、环境可用性验证
- **当前任务**：阶段 0 — 确认 Docker 安装、创建 Python 虚拟环境、安装后端/前端依赖

### 5.2 Backend Agent（后端开发）
- **职责**：`backend/` 目录，FastAPI 项目架构、API 设计、业务逻辑、Agent 编排
- **交付物**：可运行的后端服务、API 接口、数据采集调度、分析引擎
- **技术栈**：Python 3.9+ / FastAPI / SQLAlchemy / Celery/APScheduler

### 5.3 Frontend Agent（前端开发）
- **职责**：`frontend/` 目录，React + Vite + TypeScript 前端应用
- **交付物**：Dashboard 页面、金融图表、预测展示、报告页面
- **技术栈**：React 18 / TypeScript / Vite / ECharts

### 5.4 Database Agent（数据库）
- **职责**：`database/` 目录，PostgreSQL Schema 设计与 Migration
- **交付物**：数据库表结构、Migration 脚本、数据字典、索引优化
- **设计原则**：所有数据保留来源/时间戳/质量状态，预测可追溯

### 5.5 部署 Agent
- **职责**：Docker 容器管理、服务编排、部署流程
- **交付物**：docker-compose 配置更新、部署文档、环境一致性保障
- **当前任务**：阶段 0 — 确认 Docker Desktop 安装并验证容器可用性

### 5.6 版本管理 Agent（Git）
- **职责**：Git 规范、分支策略、提交规范、合并管理
- **交付物**：Git 工作流文档、分支策略、提交历史管理
- **规则**：提交信息必须使用 feat/fix/test/docs/refactor/chore 前缀

### 5.7 PM Agent（总控 — 由我担任）
- **职责**：需求拆解、架构边界、任务拆分、依赖协调、验收、质量把控
- **原则**：每个功能完成后必须自测 → Git 提交 → PM 验收 → 才进入下一阶段

---

## 六、核心工作流

```
外部数据源
    ↓
数据采集（Data Agent）
    ↓
原始数据保存 → 数据质量检查（DataQA Agent）
    ↓
标准化/清洗 → 指标计算
    ↓
专业 Agent 并行分析
├── Technical Agent（技术面：MA/RSI/MACD/布林带等）
├── Macro Agent（宏观面：Fed/通胀/就业/利率等）
├── Market Agent（市场面：美元/美债/原油/美股/VIX等）
├── Fund Agent（资金面：ETF/CFTC/央行购金等）
└── Geo Agent（地缘政治：新闻/冲突/风险事件等）
    ↓
量化模型/统计分析（Quant Agent）
    ↓
DeepSeek 综合分析（DeepSeek Agent）
    ↓
决策融合（Decision Agent）
    ↓
短期预测 + 长期预测 + 研究报告
    ↓
Backend API → Frontend 展示
    ↓
历史记录/回测 → QA → 发布
```

---

## 七、监测指标体系（14 大类）

1. **黄金本身** — 现货/期货价格、涨跌幅、成交量、持仓量、波动率
2. **美联储与利率** — FOMC、联邦基金利率、政策声明、点阵图
3. **通胀** — CPI、核心 CPI、PCE、PPI、通胀预期
4. **就业与经济** — 非农、失业率、GDP、PMI、零售销售等
5. **美元** — DXY、EUR/USD、USD/JPY、USD/CNH
6. **美债** — 2Y/5Y/10Y/30Y、TIPS、实际收益率、收益率曲线
7. **原油** — WTI、Brent、库存、OPEC
8. **美股与风险** — S&P 500、Nasdaq、VIX 等
9. **黄金资金面** — ETF 流入流出、CFTC 持仓
10. **全球央行** — 黄金储备变化、购金/售金趋势
11. **地缘政治** — 战争、冲突、制裁、金融风险事件
12. **技术面** — MA/RSI/MACD/布林带/ADX/Fibonacci 等
13. **其他贵金属** — 白银、铂金、钯金
14. **工业金属** — 铜、铝、锌、镍、铅、锡

---

## 八、预测输出标准

### 短期预测（1小时～5天）
- 趋势：偏多/中性/偏空
- 上涨/下跌/震荡概率
- 置信度
- 5 个支撑位 S1-S5（含依据）
- 5 个阻力位 R1-R5（含依据）
- 主要利多/利空因素、预测失效条件

### 长期预测（1～12个月）
- Bear/Base/Bull 三种情景
- 各情景概率与目标价格区间
- 核心驱动因素与风险

### 研究报告
- 先展示数据事实，再给分析结论
- 必须区分：事实 / 模型输出 / AI推断 / 不确定性
- 每个结论必须可追溯到数据和指标

---

## 九、协作规则

1. **一次只做一个明确的小任务**，不大范围重构
2. **自检通过才能提交**：编译/启动通过、测试通过、日志正常
3. **PM 验收后才进入下一步**
4. **不跨目录修改**：需要跨模块时先报告 PM
5. **敏感信息禁止提交 Git**：API Key、密码等只写 `.env`
6. **所有预测必须保留生成时间和输入数据版本**，方便追溯
7. **提交信息格式**：`feat/fix/test/docs/refactor/chore: 描述`

---

## 十、当前项目状态

### 已完成
- [x] 项目需求文档与技术栈文档确认
- [x] 基础设施配置文件（docker-compose.yml、.env、.gitignore）
- [x] 项目一级目录骨架（backend/、frontend/、database/、docs/）
- [x] 环境检查报告（见 docs/environment/environment-report.md）

### 当前环境
| 工具 | 状态 | 版本 |
|------|------|------|
| Git | ✅ | 2.47.1 |
| Python | ✅ | 3.9.13 |
| Node.js | ✅ | 20.20.2 |
| npm | ✅ | 10.8.2 |
| Docker | ❌ 未安装 | — |

### 当前阻塞项
- **Docker 未安装**：PostgreSQL 和 Redis 容器无法启动，需用户手动安装 Docker Desktop

### 下一步
1. 环境配置 Agent 完成环境配置（包括 Docker 安装确认）
2. Backend Agent 初始化 FastAPI 项目
3. Frontend Agent 初始化 React + Vite 项目
4. Database Agent 设计数据库 Schema
5. 版本管理 Agent 完成首次规范提交

---

## 十一、环境配置说明

### 环境变量
- 所有配置在 `.env` 文件中（不提交 Git）
- 模板在 `.env.example` 中
- DeepSeek API Key 需要用户提供

### 本地服务端口（规划）
| 服务 | 端口 |
|------|------|
| Backend API | 8000 |
| Frontend | 5173 |
| PostgreSQL | 5432 |
| Redis | 6379 |

### Docker 服务
- PostgreSQL 16 (Alpine) — 容器名 `goldsight-postgres`
- Redis 7 (Alpine) — 容器名 `goldsight-redis`
- 启动命令：`docker compose up -d`
