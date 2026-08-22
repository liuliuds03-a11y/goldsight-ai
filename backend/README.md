# GoldSight Backend

GoldSight AI V3.0 后端服务，基于 **Python + FastAPI** 构建。

## 职责

- RESTful API 服务，为前端提供数据、指标、预测、报告和告警接口
- 数据采集调度与任务管理
- 专业 Agent 分析编排（技术面、宏观面、资金面、地缘政治等）
- DeepSeek 大模型综合分析集成
- 量化模型与预测融合
- 研究报告自动生成

## 技术栈

- **框架**: FastAPI
- **语言**: Python 3.9+
- **数据库**: PostgreSQL 16（通过 Docker 提供）
- **缓存**: Redis 7（通过 Docker 提供）
- **依赖管理**: pip + requirements.txt（项目虚拟环境隔离）

## 目录结构

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口
│   ├── core/                # 核心模块
│   │   ├── config.py        # 配置管理 (pydantic-settings)
│   │   ├── database.py      # PostgreSQL 异步连接 (SQLAlchemy)
│   │   ├── redis_client.py  # Redis 异步连接
│   │   ├── response.py      # 统一响应格式
│   │   └── exceptions.py    # 统一异常处理
│   ├── api/                 # API 路由层
│   │   ├── router.py        # v1 路由汇总
│   │   └── v1/
│   │       └── health.py    # 健康检查端点
│   ├── models/              # SQLAlchemy ORM 模型（待扩展）
│   ├── schemas/             # Pydantic 数据模型（待扩展）
│   └── services/            # 业务逻辑层（待扩展）
├── tests/                   # 测试目录
│   ├── conftest.py          # 测试 fixtures
│   ├── test_health.py       # 健康检查测试
│   └── test_config.py       # 配置模块测试
└── requirements.txt         # 依赖清单
```

## 启动方式

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 环境变量

参考项目根目录 `.env.example`，后端相关配置包括：

- `POSTGRES_*` — 数据库连接
- `REDIS_*` — 缓存连接
- `DEEPSEEK_API_KEY` / `DEEPSEEK_API_BASE_URL` / `DEEPSEEK_MODEL` — AI 模型
- `BACKEND_HOST` / `BACKEND_PORT` / `BACKEND_LOG_LEVEL` — 服务配置
- `JWT_SECRET_KEY` / `JWT_ALGORITHM` / `JWT_ACCESS_TOKEN_EXPIRE_MINUTES` — 认证
