# GoldSight 前端第一阶段自检报告

> 自检时间：2026-08-22 | Frontend Agent

---

## 一、自检结果总览

| 检查项 | 状态 | 说明 |
|--------|------|------|
| npm install | ✅ 通过 | 所有依赖安装成功，无报错 |
| npm run dev | ✅ 通过 | Vite 开发服务器在 305ms 内启动，监听 http://localhost:5173/ |
| npm run build | ✅ 通过 | TypeScript 编译 + Vite 打包均成功，产物 291KB (gzip 98KB) |
| TypeScript 错误 | ✅ 无 | tsc -b 编译通过，零错误 |
| 控制台报错 | ✅ 无 | 启动过程无 warning/error |

---

## 二、技术栈确认

| 项目 | 选型 | 版本 |
|------|------|------|
| 框架 | React | 18.3.x |
| 语言 | TypeScript | 5.6.x |
| 构建工具 | Vite | 6.4.x |
| 图表库 | ECharts | 已安装 |
| 路由 | React Router | v6 (已安装) |
| HTTP 客户端 | Axios | 已安装 |
| 状态管理 | Zustand | 已安装 |
| 包管理器 | npm | 10.8.2 |

---

## 三、目录结构

```
frontend/
├── public/                  # 静态资源
│   └── vite.svg            # 站点图标
├── src/
│   ├── assets/             # 资源文件（图片等）
│   ├── components/
│   │   └── layout/         # 布局组件（Header / Footer / Layout）
│   ├── hooks/              # 自定义 Hooks（待填充）
│   ├── pages/              # 页面组件
│   │   ├── Dashboard.tsx   # 首页 Dashboard（含健康检查）
│   │   ├── Gold.tsx        # 黄金详情（占位）
│   │   ├── Prediction.tsx  # 预测分析（占位）
│   │   ├── Report.tsx      # 研究报告（占位）
│   │   ├── News.tsx        # 新闻资讯（占位）
│   │   └── PlaceholderPage.tsx  # 通用占位组件
│   ├── services/           # API 服务层
│   │   ├── client.ts       # Axios 封装（拦截器/统一错误处理）
│   │   ├── health.ts       # 健康检查接口
│   │   └── index.ts        # 统一导出
│   ├── stores/             # Zustand 状态管理
│   │   └── appStore.ts     # 全局应用状态
│   ├── styles/
│   │   └── global.css      # 全局样式（暗色主题）
│   ├── types/              # TypeScript 类型定义
│   │   └── api.ts          # API 响应/请求类型
│   ├── App.tsx             # 根组件
│   ├── main.tsx            # 入口文件
│   ├── router.tsx          # 路由配置
│   └── vite-env.d.ts       # Vite 环境变量类型
├── .env                    # 前端环境变量
├── eslint.config.js        # ESLint 配置
├── index.html              # HTML 入口
├── package.json            # 项目配置
├── tsconfig.json           # TypeScript 配置
├── tsconfig.app.json       # 应用 TS 配置
├── tsconfig.node.json      # Node TS 配置
├── vite.config.ts          # Vite 配置（含代理）
└── README.md               # 项目说明
```

---

## 四、已实现功能

### 4.1 基础布局
- **顶部导航栏**：GoldSight AI Logo + 5 个导航项 + 版本号
- **主内容区**：最大宽度 1400px，居中显示
- **页脚**：版权信息 + 投资风险提示

### 4.2 路由系统
- `/` — Dashboard 首页
- `/gold` — 黄金详情页
- `/prediction` — 预测分析页
- `/report` — 研究报告页
- `/news` — 新闻资讯页
- 所有非 Dashboard 页面均为占位页面，后续填充

### 4.3 API 服务层
- Axios 实例封装，baseURL 从环境变量读取
- 请求拦截器（预留 token 注入）
- 响应拦截器（统一业务错误/HTTP 错误处理）
- 封装 get/post/put/del 方法
- 健康检查接口调用示例

### 4.4 Dashboard 健康检查
- 页面加载时自动调用 `GET /api/v1/health`
- 展示连接状态：checking（黄色闪烁）/ connected（绿色）/ disconnected（红色）
- 展示后端服务名称和状态

### 4.5 开发代理
- Vite 代理配置：`/api` → 后端 origin
- 从项目根目录 `.env` 读取 `VITE_API_BASE_URL`

---

## 五、构建产物

```
dist/
├── index.html              0.51 kB (gzip 0.37 kB)
├── assets/
│   ├── index-*.css         4.82 kB (gzip 1.42 kB)
│   └── index-*.js        291.12 kB (gzip 98.29 kB)
```

---

## 六、后续计划

1. 接入真实后端数据 API，丰富 Dashboard 内容
2. 实现 ECharts K线图组件
3. 实现技术指标图表（MA/RSI/MACD/布林带）
4. 添加预测结果可视化页面
5. 添加研究报告展示页面
6. 响应式适配优化
