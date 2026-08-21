# GoldSight Frontend

GoldSight AI V3.0 前端应用，基于 **TypeScript + React + Vite** 构建。

## 职责

- 金融 Dashboard 展示（黄金状态、关键驱动因素、技术指标）
- K 线图、指标图、趋势图等 ECharts 金融图表
- 短期/长期预测结果可视化（概率、支撑/阻力位、情景分析）
- AI 研究报告展示
- 新闻与地缘政治事件展示

## 技术栈

- **框架**: React 18 + TypeScript
- **构建工具**: Vite
- **图表**: ECharts
- **状态管理**: 待定（由 Frontend Agent 确认）
- **包管理器**: npm

## 目录结构

> 由 Frontend Agent 自主设计并逐步完善。

## 启动方式

```bash
cd frontend
npm install
npm run dev
```

## 环境变量

参考项目根目录 `.env.example`，前端相关配置包括：

- `FRONTEND_PORT` — 开发服务器端口（默认 5173）
- `VITE_API_BASE_URL` — 后端 API 地址（默认 `http://localhost:8000/api/v1`）
