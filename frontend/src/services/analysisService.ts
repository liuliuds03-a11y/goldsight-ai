import { get, post } from './client'
import type {
  AnalysisResult,
  AnalysisSummary,
  DataQueryResponse,
} from '@/types'

/** 触发跨市场分析 */
export function triggerMarketAnalysis() {
  return post<AnalysisResult>('/analysis/market')
}

/** 触发宏观分析 */
export function triggerMacroAnalysis() {
  return post<AnalysisResult>('/analysis/macro')
}

/** 查询跨市场分析结果 */
export function fetchMarketAnalysis(limit = 1) {
  return get<DataQueryResponse<AnalysisResult>>('/analysis/market', { limit })
}

/** 查询宏观分析结果 */
export function fetchMacroAnalysis(limit = 1) {
  return get<DataQueryResponse<AnalysisResult>>('/analysis/macro', { limit })
}

/** 获取分析综合摘要 */
export function fetchAnalysisSummary() {
  return get<AnalysisSummary>('/analysis/summary')
}
