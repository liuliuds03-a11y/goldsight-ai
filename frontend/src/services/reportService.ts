import { get } from './client'

/* ── 每日报告数据类型 ─────────────────────────────────── */

/** 市场快照 - 贵金属 */
export interface SnapshotMetal {
  price: number
  unit: string
  date: string
  source: string
}

/** 市场快照 - 美元汇率 */
export interface SnapshotUsdRates {
  EUR: number
  JPY: number
  GBP: number
  CHF: number
  CNY: number
}

/** 市场快照 - 通用指标 */
export interface SnapshotIndicator {
  value: number
  unit: string
  date: string
}

/** 市场快照 - 简单值指标 */
export interface SnapshotSimple {
  value: number
  date: string
}

/** 市场快照 */
export interface MarketSnapshot {
  gold: SnapshotMetal
  silver: SnapshotMetal
  gold_silver_ratio: number | null
  usd_rates: SnapshotUsdRates
  treasury_10y: SnapshotIndicator
  wti_oil: { price: number; unit: string; date: string }
  sp500: SnapshotSimple
  fed_rate: SnapshotIndicator
  vix: SnapshotSimple
}

/** 分析摘要单项 */
export interface AnalysisSummaryItem {
  conclusion: string
  score: number
  confidence: number
}

/** 分析摘要 */
export interface AnalysisSummaryReport {
  market: AnalysisSummaryItem
  macro: AnalysisSummaryItem
  ai_prediction: AnalysisSummaryItem
}

/** 每日报告 */
export interface DailyReport {
  date: string
  generated_at: string
  market_snapshot: MarketSnapshot
  analysis_summary: AnalysisSummaryReport
  _cached: boolean
}

/** 历史报告摘要 */
export interface ReportHistoryItem {
  date: string
  gold_price: number | null
  ai_conclusion: string | null
  generated_at: string
}

/** 历史报告列表响应 */
export interface ReportHistoryResponse {
  reports: ReportHistoryItem[]
  total: number
}

/** 获取每日报告 */
export function fetchDailyReport(date?: string) {
  return get<DailyReport>('/reports/daily', date ? { date } : undefined)
}

/** 获取历史报告列表 */
export function fetchReportHistory(limit?: number) {
  return get<ReportHistoryResponse>('/reports/history', limit ? { limit } : undefined)
}
