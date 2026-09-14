# GoldSight AI — 全球多金属智能监测与分析平台

<p align="center">
  <img src="https://img.shields.io/badge/version-3.0-d4a017?style=flat-square" alt="Version">
  <img src="https://img.shields.io/badge/python-3.9+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black" alt="React">
  <img src="https://img.shields.io/badge/FastAPI-0.100-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
  <img src="https://img.shields.io/badge/PostgreSQL-16-4169E1?style=flat-square&logo=postgresql&logoColor=white" alt="PostgreSQL">
  <img src="https://img.shields.io/badge/Redis-7-DC382D?style=flat-square&logo=redis&logoColor=white" alt="Redis">
  <img src="https://img.shields.io/badge/license-MIT-green?style=flat-square" alt="License">
</p>

<p align="center">
  <strong>实时金银行情 · AI 智能预测 · 跨市场关联分析 · 宏观经济监测</strong>
</p>

---

## 项目简介

GoldSight AI 是一个面向贵金属投资者的智能监测平台，整合全球多源金融数据，通过 AI 大模型进行价格预测与风险评估。系统涵盖实时行情、技术指标、基本面分析、宏观经济指标、金融压力监测等核心功能。

### 核心亮点

- **实时行情** — 金银价格、美元指数、美债收益率、原油、股指等 8+ 资产类别实时追踪
- **AI 预测** — 基于 DeepSeek 大模型的多因素价格预测，24 小时智能缓存
- **技术分析** — 18 种技术指标（MA/EMA/MACD/RSI/布林带/ADX 等），K 线/折线图切换
- **基本面** — 金银供需格局、央行储备、工业需求等深度基本面信息
- **宏观经济** — CPI/PPI/GDP/非农/PMI/零售销售等 10+ 经济指标历史趋势图
- **金融压力** — VIX、实际收益率、信用利差、美元指数的综合压力监测
- **新闻聚合** — Kitco/Reuters/CNBC/MarketWatch 多源 RSS 智能分类聚合
- **研究报告** — 跨市场 + 宏观 + AI 三维分析日报

## 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (React 18 + TypeScript)       │
│  Vite · ECharts · React Router · Axios                   │
│  6 页面：总览 / 黄金 / 白银 / 预测 / 报告 / 新闻         │
└────────────────────────┬────────────────────────────────┘
                         │ HTTP /api/v1
┌────────────────────────┴────────────────────────────────┐
│                    Backend (FastAPI + Python 3.9+)        │
│  实时数据接口 · 采集框架 · 技术指标 · AI 预测 · 新闻聚合  │
│  Redis 缓存 (5min TTL) · DeepSeek API 集成               │
└───────┬────────────────────────────────┬────────────────┘
        │                                │
┌───────┴──────────┐          ┌──────────┴───────────────┐
│  PostgreSQL 16   │          │       Redis 7            │
│  22 张数据表      │          │  实时缓存 · 新闻缓存     │
│  技术指标 · 历史  │          │  预测结果缓存 (24h)      │
└──────────────────┘          └──────────────────────────┘
```

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| **前端** | React 18 + TypeScript + Vite | 暗色金色主题，ECharts 图表 |
| **后端** | FastAPI + SQLAlchemy async | 异步 API，自动 OpenAPI 文档 |
| **数据库** | PostgreSQL 16 | 22 张表，覆盖全业务 |
| **缓存** | Redis 7 | 多级 TTL 缓存策略 |
| **AI** | DeepSeek API | 智能预测 + 风险评估 |
| **数据源** | gold-api.com / FRED / Frankfurter / RSS | 免费公开 API |

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 18+
- PostgreSQL 16
- Redis 7

### 1. 克隆项目

```bash
git clone https://github.com/your-username/goldsight-ai.git
cd goldsight-ai
```

### 2. 后端启动

```bash
# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate    # Windows
# source .venv/bin/activate  # Linux/Mac

# 安装依赖
cd backend
pip install -r requirements.txt

# 配置环境变量
cp ../.env.example ../.env
# 编辑 .env 填入数据库连接信息

# 启动服务
uvicorn app.main:app --host 0.0.0.0 --port 8016 --reload
```

### 3. 前端启动

```bash
cd frontend
npm install
npm run dev
# 访问 http://localhost:5173
```

### 4. Docker 部署（推荐）

```bash
docker-compose up -d
```

## 项目结构

```
GoldSight Multi-Metal/
├── backend/                    # 后端服务
│   ├── app/
│   │   ├── api/v1/            # API 端点
│   │   │   ├── realtime.py    # 实时数据接口 (12+ 端点)
│   │   │   ├── data.py        # 数据查询接口
│   │   │   ├── prediction.py  # AI 预测接口
│   │   │   ├── news.py        # 新闻聚合接口
│   │   │   └── analysis.py    # 分析结果接口
│   │   ├── services/
│   │   │   ├── data_collection/  # 数据采集框架
│   │   │   │   ├── base_collector.py    # 采集器基类
│   │   │   │   ├── registry.py          # 采集器注册表
│   │   │   │   ├── pipeline.py          # 采集流水线
│   │   │   │   └── collectors/          # 8 个采集器
│   │   │   ├── analysis/      # 跨市场 + 宏观分析
│   │   │   └── prediction/    # DeepSeek AI 预测
│   │   ├── core/              # 数据库、Redis、配置
│   │   └── models/            # SQLAlchemy ORM 模型
│   └── requirements.txt
├── frontend/                   # 前端应用
│   ├── src/
│   │   ├── pages/             # 6 个页面组件
│   │   ├── components/        # 布局组件 (Header/Footer/Layout)
│   │   ├── services/          # API 服务层
│   │   ├── types/             # TypeScript 类型定义
│   │   ├── utils/             # 通用工具函数
│   │   └── styles/            # 全局样式
│   └── package.json
├── database/                   # 数据库迁移脚本
│   └── migrations/            # SQL 迁移文件 (22 张表)
├── docker-compose.yml          # Docker 编排
├── .env.example                # 环境变量模板
└── .github/workflows/          # CI/CD 流水线
```

## 页面展示

| 页面 | 功能 |
|------|------|
| **总览** | 实时金银价格、4 大关键指标、AI 预测摘要、5 大经济指标趋势图、金融压力监测 |
| **黄金** | K 线/折线图切换、MA5/20/60 均线叠加、交易记录、基本面概览 |
| **白银** | 120 天价格走势图、交易记录、金银比分析、基本面概览 |
| **预测** | AI 预测方向/目标价/置信度、支撑阻力位、风险因素、历史趋势图 |
| **报告** | 9 大市场快照指标、跨市场+宏观+AI 三维分析、历史报告 |
| **新闻** | 多源 RSS 聚合、分类/来源筛选、智能关键词匹配 |

## 数据采集框架

采用**开闭原则**设计的可扩展采集框架：

```python
# 新增采集器只需 3 步：
# 1. 继承 BaseCollector
# 2. 实现 fetch() + clean() 方法
# 3. 自动注册到 CollectorRegistry

class MyCollector(BaseCollector):
    async def fetch(self, **kwargs) -> List[Dict]: ...
    def clean(self, raw_data) -> List[Dict]: ...
```

当前已注册 8 个采集器：Gold、Silver、USD、Treasury、Oil、Stock、Economic、VIX。

## 开发命令

```bash
# 前端
npm run dev          # 开发服务器
npm run build        # 生产构建
npm run preview      # 预览构建

# 后端
uvicorn app.main:app --reload          # 开发模式
pytest tests/ -v                        # 运行测试

# 数据采集
curl -X POST http://localhost:8016/api/v1/data/collect/GoldPriceCollector
```

## API 文档

启动后端后访问：
- Swagger UI: `http://localhost:8016/docs`
- ReDoc: `http://localhost:8016/redoc`

## 贡献

欢迎提交 Issue 和 Pull Request。

## 许可证

[MIT License](LICENSE)

## 免责声明

本系统仅供学习和研究参考，不构成任何投资建议。投资有风险，入市需谨慎。
