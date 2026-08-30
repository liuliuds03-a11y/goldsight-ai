export { get, post, put, del } from './client'
export { fetchHealth } from './health'
export {
  fetchGoldPrices,
  fetchUsdData,
  fetchTreasuryYields,
  fetchOilData,
  fetchStockMarketData,
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