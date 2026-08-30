import { get, post } from './client'
import type { PredictionResult, AISummary, DataQueryResponse } from '@/types'

/** 触发 AI 黄金价格预测 */
export function triggerGoldPrediction() {
  return post<PredictionResult>('/predict/gold')
}

/** 查询 AI 预测结果 */
export function fetchGoldPrediction(limit: number = 10) {
  return get<DataQueryResponse<PredictionResult>>('/predict/gold', { limit })
}

/** AI 综合摘要 — 一句话总结当前行情 */
export function triggerAISummary() {
  return post<AISummary>('/predict/summary')
}

/** 查询历史预测记录（分页） */
export function fetchPredictionHistory(page: number = 1, pageSize: number = 20) {
  return get<DataQueryResponse<PredictionResult>>('/predict/gold', {
    page,
    pageSize,
  })
}
