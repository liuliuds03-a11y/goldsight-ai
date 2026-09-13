export { get, post, put, del } from './client'
export { fetchHealth } from './health'
export {
  fetchGoldPrices,
  fetchUsdData,
  fetchTreasuryYields,
  fetchOilData,
  fetchStockMarketData,
  fetchPreciousMetals,
  fetchIndicators,
  triggerIndicatorCalculation,
  fetchDataStats,
} from './goldService'
export {
  triggerMarketAnalysis,
  triggerMacroAnalysis,
  fetchMarketAnalysis,
  fetchMacroAnalysis,
  fetchAnalysisSummary,
} from './analysisService'
export {
  triggerGoldPrediction,
  fetchGoldPrediction,
  triggerAISummary,
  fetchPredictionHistory,
} from './predictService'
export type { PredictionTriggerResult } from './predictService'
export {
  fetchRealtimeAll,
  fetchRealtimeGold,
  fetchRealtimeUSD,
  fetchRealtimeTreasury,
  fetchRealtimeOil,
  fetchRealtimeStock,
  refreshRealtime,
} from './realtimeService'
export type {
  RealtimeGold,
  RealtimeUSD,
  RealtimeTreasury,
  RealtimeOil,
  RealtimeStock,
  RealtimeAll,
} from './realtimeService'
export {
  fetchDailyReport,
  fetchReportHistory,
} from './reportService'
export type {
  DailyReport,
  MarketSnapshot,
  AnalysisSummaryReport,
  ReportHistoryItem,
} from './reportService'