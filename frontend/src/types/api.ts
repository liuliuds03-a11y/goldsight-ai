/** 后端统一响应格式 */
export interface ApiResponse<T = unknown> {
  code: number
  message?: string
  data: T
}

/** 健康检查数据 */
export interface HealthData {
  status: string
  service: string
}

/** 通用分页参数 */
export interface PaginationParams {
  page?: number
  pageSize?: number
}

/** 通用分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}

/* ── 数据查询通用 ─────────────────────────────────────── */

/** 数据表查询通用响应 */
export interface DataQueryResponse<T> {
  records: T[]
  total: number
  limit: number
  offset: number
}

/* ── 黄金价格 ─────────────────────────────────────────── */

/** 黄金价格记录 */
export interface GoldPriceRecord {
  id: number
  timestamp: string
  price_type: string
  symbol: string
  open: number | null
  high: number | null
  low: number | null
  close: number | null
  change_value: number | null
  change_pct: number | null
  volume: number | null
  source: string
  collected_at: string
  quality_status: string
}

/* ── 美元数据 ─────────────────────────────────────────── */

/** 美元数据记录 */
export interface UsdDataRecord {
  id: number
  timestamp: string
  pair: string
  open: number | null
  high: number | null
  low: number | null
  close: number | null
  change_value: number | null
  change_pct: number | null
  source: string
  collected_at: string
  quality_status: string
}

/* ── 国债收益率 ───────────────────────────────────────── */

/** 国债收益率记录 */
export interface TreasuryYieldRecord {
  id: number
  timestamp: string
  maturity: string
  yield: number | null
  real_yield: number | null
  spread_to_10y: number | null
  source: string
  collected_at: string
  quality_status: string
}

/* ── 原油数据 ─────────────────────────────────────────── */

/** 原油数据记录 */
export interface OilDataRecord {
  id: number
  timestamp: string
  oil_type: string
  open: number | null
  high: number | null
  low: number | null
  close: number | null
  change_value: number | null
  change_pct: number | null
  source: string
  collected_at: string
  quality_status: string
}

/* ── 股票市场 ─────────────────────────────────────────── */

/** 股票市场记录 */
export interface StockMarketRecord {
  id: number
  timestamp: string
  index_symbol: string
  open: number | null
  high: number | null
  low: number | null
  close: number | null
  change_value: number | null
  change_pct: number | null
  source: string
  collected_at: string
  quality_status: string
}

/* ── 技术指标 ─────────────────────────────────────────── */

/** 技术指标记录 */
export interface TechnicalIndicatorRecord {
  id: number
  timestamp: string
  symbol: string
  indicator_name: string
  period: string | null
  category: string | null
  value: number | null
  extra_data: Record<string, unknown> | null
  source: string
  collected_at: string
  quality_status: string
}

/* ── 分析模块 ─────────────────────────────────────────── */

/** 分析因素 */
export interface AnalysisFactor {
  name: string
  impact: string
  weight?: number
  evidence: string
  score: number
}

/** 分析数据范围 */
export interface AnalysisDataRange {
  start?: string
  end?: string
}

/** 分析结果 */
export interface AnalysisResult {
  id?: number
  analysis_type: string
  generated_at?: string
  conclusion: string
  confidence: number
  score: number
  factors: AnalysisFactor[]
  data_range: AnalysisDataRange
  source?: string
  metadata?: Record<string, unknown>
  timestamp?: string
}

/** 综合摘要 */
export interface AnalysisSummary {
  timestamp: string
  market_analysis: AnalysisResult | null
  macro_analysis: AnalysisResult | null
  overall_conclusion: string
  overall_score: number
  overall_confidence: number
}

/* ── AI 预测 ──────────────────────────────────────────── */

/** AI 预测关键价位 */
export interface PredictionKeyLevels {
  support: number
  resistance: number
}

/** AI 预测结果 */
export interface PredictionResult {
  id?: number
  analysis_type: string
  generated_at?: string
  conclusion: string
  confidence: number
  score: number
  factors: AnalysisFactor[]
  data_range: {
    prediction_type?: string
    time_horizon?: string
    target_price?: number
  }
  source?: string
  metadata?: Record<string, unknown>
}

/** AI 行情摘要 */
export interface AISummary {
  summary: string
  context?: string
  generated_at: string
  is_fallback: boolean
}

/* ── 数据统计 ─────────────────────────────────────────── */

/** 数据统计概览 */
export interface DataStats {
  table_counts: Record<string, number | string>
}
