import { useCallback, useEffect, useState } from 'react'
import {
  fetchRealtimeAll,
  refreshRealtime,
  fetchAnalysisSummary,
  fetchGoldPrediction,
  get,
} from '@/services'
import type { RealtimeAll } from '@/services'
import type {
  AnalysisSummary,
  PredictionResult,
} from '@/types'
import './Dashboard.css'

interface EconomicData {
  nonfarm: { value: number; date: string; name: string }
  unemployment: { value: number; date: string; name: string }
  gdp: { value: number; date: string; name: string }
  ppi: { value: number; date: string; name: string }
  retail: { value: number; date: string; name: string }
}

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // 实时数据
  const [realtime, setRealtime] = useState<RealtimeAll | null>(null)
  const [economic, setEconomic] = useState<EconomicData | null>(null)
  const [analysisSummary, setAnalysisSummary] = useState<AnalysisSummary | null>(null)
  const [prediction, setPrediction] = useState<PredictionResult | null>(null)
  const [lastUpdate, setLastUpdate] = useState<string>('')

  const loadRealtimeData = useCallback(async (forceRefresh = false) => {
    try {
      if (forceRefresh) {
        setRefreshing(true)
        const res = await refreshRealtime()
        setRealtime(res.data)
      } else {
        const res = await fetchRealtimeAll()
        setRealtime(res.data)
      }
      setLastUpdate(new Date().toLocaleTimeString())
    } catch (err) {
      setError(err instanceof Error ? err.message : '实时数据加载失败')
    }
  }, [])

  const loadAnalysisData = useCallback(async () => {
    try {
      const [analysisRes, predictRes, econRes] = await Promise.all([
        fetchAnalysisSummary(),
        fetchGoldPrediction(1),
        get<EconomicData>('/realtime/economic'),
      ])
      setAnalysisSummary(analysisRes.data)
      if (predictRes.data.records.length > 0) setPrediction(predictRes.data.records[0])
      setEconomic(econRes.data)
    } catch (err) {
      console.error('分析数据加载失败:', err)
    }
  }, [])

  useEffect(() => {
    async function init() {
      setLoading(true)
      await Promise.all([loadRealtimeData(), loadAnalysisData()])
      setLoading(false)
    }
    init()
  }, [loadRealtimeData, loadAnalysisData])

  // 一键刷新所有数据
  const handleRefreshAll = async () => {
    setRefreshing(true)
    setError(null)
    await Promise.all([loadRealtimeData(true), loadAnalysisData()])
    setRefreshing(false)
  }

  const formatNumber = (value: number | null | undefined, decimals = 2) => {
    if (value == null || isNaN(value)) return '--'
    return value.toFixed(decimals)
  }

  const getTrendClass = (value: number | null | undefined) => {
    if (value == null) return 'neutral'
    return value >= 0 ? 'positive' : 'negative'
  }

  const getCachedBadge = (cached?: boolean) => {
    if (!cached) return null
    return <span className="dashboard__cached-badge">缓存</span>
  }

  return (
    <div className="dashboard">
      <div className="dashboard__header">
        <div>
          <h1 className="dashboard__title">GoldSight AI Dashboard</h1>
          <p className="dashboard__subtitle">
            全球多金属智能监测与分析平台
            {lastUpdate && <span className="dashboard__last-update"> · 最后更新 {lastUpdate}</span>}
          </p>
        </div>
        <button
          className="dashboard__refresh-btn"
          onClick={handleRefreshAll}
          disabled={refreshing}
          title="刷新所有数据"
        >
          <span className={`dashboard__refresh-icon ${refreshing ? 'spinning' : ''}`}>↻</span>
          {refreshing ? '刷新中...' : '刷新数据'}
        </button>
      </div>

      {error && (
        <div className="dashboard__error">
          <span className="dashboard__error-icon">⚠</span>
          <span>{error}</span>
          <button className="dashboard__error-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {loading && (
        <div className="dashboard__loading">
          <div className="dashboard__loading-spinner" />
          <span>正在加载数据...</span>
        </div>
      )}

      {!loading && (
        <>
          {/* 黄金实时价格卡片 */}
          <div className="dashboard__card dashboard__gold-card">
            <div className="dashboard__card-header">
              <h2 className="dashboard__card-title">黄金实时价格</h2>
              <div className="dashboard__card-actions">
                <span className="dashboard__card-badge">XAU/USD</span>
                {getCachedBadge(realtime?.gold?._cached)}
              </div>
            </div>
            <div className="dashboard__gold-content">
              <div className="dashboard__gold-price">
                ${formatNumber(realtime?.gold?.price)}
              </div>
              <div className="dashboard__gold-meta">
                <span className="dashboard__gold-source">
                  来源: {realtime?.gold?.source || '--'} · {realtime?.gold?.date || '--'}
                </span>
                <span className="dashboard__gold-gram">
                  ${formatNumber(realtime?.gold?.price_per_gram_usd)}/克
                </span>
              </div>
            </div>
          </div>

          {/* 关键指标卡片组 */}
          <div className="dashboard__grid">
            {/* 美元汇率 */}
            <div className="dashboard__indicator-card">
              <div className="dashboard__indicator-header">
                <h3 className="dashboard__indicator-title">美元汇率</h3>
                <div className="dashboard__card-actions">
                  <span className="dashboard__indicator-symbol">USD</span>
                  {getCachedBadge(realtime?.usd?._cached)}
                </div>
              </div>
              <div className="dashboard__indicator-value">
                EUR {formatNumber(realtime?.usd?.rates?.EUR, 4)}
              </div>
              <div className="dashboard__indicator-extra">
                JPY {formatNumber(realtime?.usd?.rates?.JPY, 2)} · CNY {formatNumber(realtime?.usd?.rates?.CNY, 4)}
              </div>
            </div>

            {/* 10Y 美债 */}
            <div className="dashboard__indicator-card">
              <div className="dashboard__indicator-header">
                <h3 className="dashboard__indicator-title">10Y 美债收益率</h3>
                <div className="dashboard__card-actions">
                  <span className="dashboard__indicator-symbol">US10Y</span>
                  {getCachedBadge(realtime?.treasury?._cached)}
                </div>
              </div>
              <div className="dashboard__indicator-value">
                {formatNumber(realtime?.treasury?.value, 3)}%
              </div>
              <div className="dashboard__indicator-extra">
                来源: {realtime?.treasury?.source || '--'} · {realtime?.treasury?.date || '--'}
              </div>
            </div>

            {/* 原油 */}
            <div className="dashboard__indicator-card">
              <div className="dashboard__indicator-header">
                <h3 className="dashboard__indicator-title">WTI 原油</h3>
                <div className="dashboard__card-actions">
                  <span className="dashboard__indicator-symbol">WTI</span>
                  {getCachedBadge(realtime?.oil?._cached)}
                </div>
              </div>
              <div className="dashboard__indicator-value">
                ${formatNumber(realtime?.oil?.price)}
              </div>
              <div className="dashboard__indicator-extra">
                来源: {realtime?.oil?.source || '--'} · {realtime?.oil?.date || '--'}
              </div>
            </div>

            {/* S&P500 */}
            <div className="dashboard__indicator-card">
              <div className="dashboard__indicator-header">
                <h3 className="dashboard__indicator-title">S&P 500</h3>
                <div className="dashboard__card-actions">
                  <span className="dashboard__indicator-symbol">SPX</span>
                  {getCachedBadge(realtime?.stock?._cached)}
                </div>
              </div>
              <div className="dashboard__indicator-value">
                {formatNumber(realtime?.stock?.value, 0)}
              </div>
              <div className="dashboard__indicator-extra">
                来源: {realtime?.stock?.source || '--'} · {realtime?.stock?.date || '--'}
              </div>
            </div>
          </div>

          {/* 经济指标卡片组 */}
          {economic && (
            <div className="dashboard__card">
              <div className="dashboard__card-header">
                <h2 className="dashboard__card-title">经济指标</h2>
                <span className="dashboard__card-badge">FRED</span>
              </div>
              <div className="dashboard__economic-grid">
                <div className="dashboard__economic-item">
                  <span className="dashboard__economic-label">非农就业</span>
                  <span className="dashboard__economic-value">
                    {economic.nonfarm?.value ? `${(economic.nonfarm.value / 1000).toFixed(1)}M` : '--'}
                  </span>
                  <span className="dashboard__economic-meta">
                    {economic.nonfarm?.date || '--'}
                  </span>
                </div>
                <div className="dashboard__economic-item">
                  <span className="dashboard__economic-label">失业率</span>
                  <span className="dashboard__economic-value">
                    {economic.unemployment?.value != null ? `${economic.unemployment.value}%` : '--'}
                  </span>
                  <span className="dashboard__economic-meta">
                    {economic.unemployment?.date || '--'}
                  </span>
                </div>
                <div className="dashboard__economic-item">
                  <span className="dashboard__economic-label">GDP 增速</span>
                  <span className="dashboard__economic-value">
                    {economic.gdp?.value != null ? `${economic.gdp.value}%` : '--'}
                  </span>
                  <span className="dashboard__economic-meta">
                    {economic.gdp?.date || '--'}
                  </span>
                </div>
                <div className="dashboard__economic-item">
                  <span className="dashboard__economic-label">PPI 通胀</span>
                  <span className="dashboard__economic-value">
                    {economic.ppi?.value != null ? economic.ppi.value.toFixed(1) : '--'}
                  </span>
                  <span className="dashboard__economic-meta">
                    {economic.ppi?.date || '--'}
                  </span>
                </div>
                <div className="dashboard__economic-item">
                  <span className="dashboard__economic-label">零售销售</span>
                  <span className="dashboard__economic-value">
                    {economic.retail?.value ? `${(economic.retail.value / 1000).toFixed(0)}B` : '--'}
                  </span>
                  <span className="dashboard__economic-meta">
                    {economic.retail?.date || '--'}
                  </span>
                </div>
              </div>
            </div>
          )}

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
