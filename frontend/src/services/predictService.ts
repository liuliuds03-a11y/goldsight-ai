import { get, post } from './client'
import type { PredictionResult, AISummary, DataQueryResponse } from '@/types'

/** POST /predict/gold 响应（含缓存状态） */
export interface PredictionTriggerResult {
  record: PredictionResult
  cached: boolean
  message?: string
}

/** 触发 AI 黄金价格预测（默认检查 24h 缓存） */
export function triggerGoldPrediction(force = false) {
  return post<PredictionTriggerResult>(`/predict/gold?force=${force}`)
}

/** 查询 AI 预测结果（从数据库读取缓存） */
export function fetchGoldPrediction(limit: number = 10) {
  return get<DataQueryResponse<PredictionResult>>('/predict/gold', { limit })
}

/** AI 综合摘要 — 一句话总结当前行情（手动触发，不自动调用） */
export function triggerAISummary(force = false) {
  return post<AISummary>(`/predict/summary?force=${force}`)
}

/** 查询历史预测记录（分页） */
export function fetchPredictionHistory(page: number = 1, pageSize: number = 20) {
  return get<DataQueryResponse<PredictionResult>>('/predict/gold', {
    page,
    pageSize,
  })
}
