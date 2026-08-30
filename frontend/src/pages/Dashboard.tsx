import { useEffect, useState } from 'react'
import {
  fetchGoldPrices,
  fetchUsdData,
  fetchTreasuryYields,
  fetchOilData,
  fetchStockMarketData,
  fetchAnalysisSummary,
  fetchGoldPrediction,
} from '@/services'
import type {
  GoldPriceRecord,
  UsdDataRecord,
  TreasuryYieldRecord,
  OilDataRecord,
  StockMarketRecord,
  AnalysisSummary,
  PredictionResult,
} from '@/types'
import './Dashboard.css'

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // 数据状态
  const [goldPrice, setGoldPrice] = useState<GoldPriceRecord | null>(null)
  const [usdData, setUsdData] = useState<UsdDataRecord | null>(null)
  const [treasuryYield, setTreasuryYield] = useState<TreasuryYieldRecord | null>(null)
  const [oilData, setOilData] = useState<OilDataRecord | null>(null)
  const [stockData, setStockData] = useState<StockMarketRecord | null>(null)
  const [analysisSummary, setAnalysisSummary] = useState<AnalysisSummary | null>(null)
  const [prediction, setPrediction] = useState<PredictionResult | null>(null)

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true)
        setError(null)

        // 并行请求所有数据
        const [goldRes, usdRes, treasuryRes, oilRes, stockRes, analysisRes, predictRes] = await Promise.all([
          fetchGoldPrices({ limit: 1 }),
          fetchUsdData({ limit: 1 }),
          fetchTreasuryYields({ limit: 1, maturity: '10Y' }),
          fetchOilData({ limit: 1 }),
          fetchStockMarketData({ limit: 1, index_symbol: 'SPX' }),
          fetchAnalysisSummary(),
          fetchGoldPrediction(1),
        ])

        // 提取数据
        if (goldRes.data.records.length > 0) setGoldPrice(goldRes.data.records[0])
        if (usdRes.data.records.length > 0) setUsdData(usdRes.data.records[0])
        if (treasuryRes.data.records.length > 0) setTreasuryYield(treasuryRes.data.records[0])
        if (oilRes.data.records.length > 0) setOilData(oilRes.data.records[0])
        if (stockRes.data.records.length > 0) setStockData(stockRes.data.records[0])
        setAnalysisSummary(analysisRes.data)
        if (predictRes.data.records.length > 0) setPrediction(predictRes.data.records[0])
      } catch (err) {
        setError(err instanceof Error ? err.message : '数据加载失败')
      } finally {
        setLoading(false)
      }
    }

    loadData()
  }, [])

  // 格式化数字
  const formatNumber = (value: number | null | undefined, decimals = 2) => {
    if (value == null) return '--'
    return value.toFixed(decimals)
  }

  // 格式化涨跌幅
  const formatChange = (value: number | null | undefined) => {
    if (value == null) return '--'
    const sign = value >= 0 ? '+' : ''
    return `${sign}${value.toFixed(2)}%`
  }

  // 获取趋势箭头
  const getTrendArrow = (value: number | null | undefined) => {
    if (value == null) return '→'
    return value >= 0 ? '↑' : '↓'
  }

  // 获取趋势类名
  const getTrendClass = (value: number | null | undefined) => {
    if (value == null) return 'neutral'
    return value >= 0 ? 'positive' : 'negative'
  }

  return (
    <div className="dashboard">
      <h1 className="dashboard__title">GoldSight AI Dashboard</h1>
      <p className="dashboard__subtitle">全球多金属智能监测与分析平台</p>

      {/* 错误提示 */}
      {error && (
        <div className="dashboard__error">
          <span className="dashboard__error-icon">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="dashboard__loading">
          <div className="dashboard__loading-spinner" />
          <span>正在加载数据...</span>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* 黄金实时价格卡片 */}
          <div className="dashboard__card dashboard__gold-card">
            <div className="dashboard__card-header">
              <h2 className="dashboard__card-title">黄金实时价格</h2>
              <span className="dashboard__card-badge">XAU/USD</span>
            </div>
            <div className="dashboard__gold-content">
              <div className="dashboard__gold-price">
                ${formatNumber(goldPrice?.close)}
              </div>
              <div className={`dashboard__gold-change ${getTrendClass(goldPrice?.change_pct)}`}>
                <span className="dashboard__gold-arrow">{getTrendArrow(goldPrice?.change_pct)}</span>
                <span>{formatChange(goldPrice?.change_pct)}</span>
              </div>
            </div>
          </div>

          {/* 关键指标卡片组 */}
          <div className="dashboard__grid">
            {/* 美元指数 */}
            <div className="dashboard__indicator-card">
              <div className="dashboard__indicator-header">
                <h3 className="dashboard__indicator-title">美元指数</h3>
                <span className="dashboard__indicator-symbol">DXY</span>
              </div>
              <div className="dashboard__indicator-value">
                {formatNumber(usdData?.close, 3)}
              </div>
              <div className={`dashboard__indicator-change ${getTrendClass(usdData?.change_pct)}`}>
                {formatChange(usdData?.change_pct)}
              </div>
            </div>

            {/* 10Y 美债 */}
            <div className="dashboard__indicator-card">
              <div className="dashboard__indicator-header">
                <h3 className="dashboard__indicator-title">10Y 美债</h3>
                <span className="dashboard__indicator-symbol">US10Y</span>
              </div>
              <div className="dashboard__indicator-value">
                {formatNumber(treasuryYield?.yield, 3)}%
              </div>
              <div className="dashboard__indicator-extra">
                实际收益率: {formatNumber(treasuryYield?.real_yield, 3)}%
              </div>
            </div>

            {/* 原油 */}
            <div className="dashboard__indicator-card">
              <div className="dashboard__indicator-header">
                <h3 className="dashboard__indicator-title">原油</h3>
                <span className="dashboard__indicator-symbol">WTI</span>
              </div>
              <div className="dashboard__indicator-value">
                ${formatNumber(oilData?.close)}
              </div>
              <div className={`dashboard__indicator-change ${getTrendClass(oilData?.change_pct)}`}>
                {formatChange(oilData?.change_pct)}
              </div>
            </div>

            {/* S&P500 */}
            <div className="dashboard__indicator-card">
              <div className="dashboard__indicator-header">
                <h3 className="dashboard__indicator-title">S&P 500</h3>
                <span className="dashboard__indicator-symbol">SPX</span>
              </div>
              <div className="dashboard__indicator-value">
                {formatNumber(stockData?.close, 0)}
              </div>
              <div className={`dashboard__indicator-change ${getTrendClass(stockData?.change_pct)}`}>
                {formatChange(stockData?.change_pct)}
              </div>
            </div>
          </div>

          {/* AI 预测摘要卡片 */}
          <div className="dashboard__card dashboard__prediction-card">
            <div className="dashboard__card-header">
              <h2 className="dashboard__card-title">AI 预测摘要</h2>
              <span className="dashboard__card-badge">DeepSeek AI</span>
            </div>
            <div className="dashboard__prediction-content">
              <div className="dashboard__prediction-direction">
                <span className="dashboard__prediction-label">预测方向</span>
                <span className={`dashboard__prediction-value ${getTrendClass(prediction?.score)}`}>
                  {prediction?.conclusion || '--'}
                </span>
              </div>
              <div className="dashboard__prediction-stats">
                <div className="dashboard__prediction-stat">
                  <span className="dashboard__prediction-stat-label">置信度</span>
                  <span className="dashboard__prediction-stat-value">
                    {prediction?.confidence != null ? `${(prediction.confidence * 100).toFixed(0)}%` : '--'}
                  </span>
                </div>
                <div className="dashboard__prediction-stat">
                  <span className="dashboard__prediction-stat-label">目标价</span>
                  <span className="dashboard__prediction-stat-value">
                    ${formatNumber(prediction?.data_range?.target_price)}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* 市场分析摘要 */}
          <div className="dashboard__card dashboard__analysis-card">
            <div className="dashboard__card-header">
              <h2 className="dashboard__card-title">市场分析摘要</h2>
              <span className="dashboard__card-badge">综合分析</span>
            </div>
            <div className="dashboard__analysis-content">
              <div className="dashboard__analysis-score">
                <div className="dashboard__analysis-score-value">
                  {formatNumber(analysisSummary?.overall_score, 1)}
                </div>
                <div className="dashboard__analysis-score-label">综合评分</div>
              </div>
              <div className="dashboard__analysis-details">
                <div className="dashboard__analysis-detail">
                  <span className="dashboard__analysis-detail-label">跨市场分析</span>
                  <span className="dashboard__analysis-detail-value">
                    {formatNumber(analysisSummary?.market_analysis?.score, 1)}
                  </span>
                </div>
                <div className="dashboard__analysis-detail">
                  <span className="dashboard__analysis-detail-label">宏观分析</span>
                  <span className="dashboard__analysis-detail-value">
                    {formatNumber(analysisSummary?.macro_analysis?.score, 1)}
                  </span>
                </div>
                <div className="dashboard__analysis-detail">
                  <span className="dashboard__analysis-detail-label">置信度</span>
                  <span className="dashboard__analysis-detail-value">
                    {analysisSummary?.overall_confidence != null ? `${(analysisSummary.overall_confidence * 100).toFixed(0)}%` : '--'}
                  </span>
                </div>
              </div>
              <div className="dashboard__analysis-conclusion">
                {analysisSummary?.overall_conclusion || '暂无分析结论'}
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
