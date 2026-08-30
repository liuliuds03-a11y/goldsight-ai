import { useCallback, useEffect, useMemo, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import {
  fetchGoldPrediction,
  triggerGoldPrediction,
  fetchPredictionHistory,
} from '@/services'
import type { PredictionResult } from '@/types'
import './Prediction.css'

export default function Prediction() {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [prediction, setPrediction] = useState<PredictionResult | null>(null)
  const [cacheInfo, setCacheInfo] = useState<string>('')
  const [isCached, setIsCached] = useState(false)
  const [history, setHistory] = useState<PredictionResult[]>([])

  // 加载数据：只从数据库读缓存，不调 DeepSeek
  useEffect(() => {
    loadData()
    loadHistory()
  }, [])

  const loadHistory = useCallback(async () => {
    try {
      const res = await fetchPredictionHistory(1, 30)
      const records = res.data.records || []
      // 按时间正序排列（图表用）
      records.sort(
        (a, b) =>
          new Date(a.generated_at ?? 0).getTime() -
          new Date(b.generated_at ?? 0).getTime(),
      )
      setHistory(records)
    } catch {
      // 历史数据加载失败不影响主流程
    }
  }, [])

  async function loadData() {
    try {
      setLoading(true)
      setError(null)

      const res = await fetchGoldPrediction(1)
      if (res.data.records.length > 0) {
        setPrediction(res.data.records[0])
        setCacheInfo('来自历史预测记录')
        setIsCached(true)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '数据加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 刷新预测：后端会检查 24h 缓存，有则直接返回
  async function handleRefresh(force = false) {
    try {
      setRefreshing(true)
      setError(null)

      const result = await triggerGoldPrediction(force)
      const data = result.data
      setPrediction(data.record)
      setIsCached(data.cached)
      setCacheInfo(data.message || (data.cached ? '缓存结果' : 'AI 最新预测'))
    } catch (err) {
      setError(err instanceof Error ? err.message : '预测失败')
    } finally {
      setRefreshing(false)
    }
  }

  const formatNumber = (value: number | null | undefined, decimals = 2) => {
    if (value == null) return '--'
    return value.toFixed(decimals)
  }

  const getDirectionLabel = (score: number | null | undefined) => {
    if (score == null) return '--'
    if (score >= 70) return '看涨'
    if (score <= 30) return '看跌'
    return '震荡'
  }

  const getDirectionClass = (score: number | null | undefined) => {
    if (score == null) return 'prediction__direction--neutral'
    if (score >= 70) return 'prediction__direction--bullish'
    if (score <= 30) return 'prediction__direction--bearish'
    return 'prediction__direction--neutral'
  }

  // 从 factors 中提取 key_levels（DeepSeek 返回格式）
  const keyLevels = prediction?.factors?.find((f) => (f as any).key_levels)
  const supportLevel = (keyLevels as any)?.key_levels?.support as number | undefined
  const resistanceLevel = (keyLevels as any)?.key_levels?.resistance as number | undefined

  // 从 factors 中提取 risk_factors（DeepSeek 返回格式）
  const rawRiskFactors: string[] = prediction?.factors?.[0] && (prediction.factors[0] as any).risk_factors
    ? (prediction.factors[0] as any).risk_factors
    : []
  const riskFactors = prediction?.factors?.filter((f) => f.score < 50) || []

  /* ── 历史预测趋势图配置 ─────────────────────────────── */
  const trendChartOption = useMemo(() => {
    if (history.length === 0) return {}
    const dates = history.map((h) =>
      h.generated_at ? new Date(h.generated_at).toLocaleDateString() : '--',
    )
    const targetPrices = history.map((h) => h.data_range?.target_price ?? null)
    const confidences = history.map((h) =>
      h.confidence != null ? +(h.confidence * 100).toFixed(1) : null,
    )
    return {
      backgroundColor: '#1e2130',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(30,33,48,0.95)',
        borderColor: '#2d3040',
        textStyle: { color: '#e4e6eb', fontSize: 12 },
      },
      legend: {
        data: ['目标价', '置信度'],
        textStyle: { color: '#8b8e98', fontSize: 12 },
        top: 8,
      },
      grid: { left: 70, right: 70, top: 50, bottom: 40 },
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#2d3040' } },
        axisLabel: { color: '#8b8e98', fontSize: 11, rotate: dates.length > 10 ? 30 : 0 },
        splitLine: { show: false },
      },
      yAxis: [
        {
          type: 'value',
          name: '目标价 ($)',
          nameTextStyle: { color: '#8b8e98', fontSize: 11 },
          scale: true,
          axisLine: { show: false },
          axisLabel: { color: '#8b8e98', fontSize: 11, formatter: (v: number) => v.toFixed(0) },
          splitLine: { lineStyle: { color: '#2d3040', type: 'dashed' } },
        },
        {
          type: 'value',
          name: '置信度 (%)',
          nameTextStyle: { color: '#8b8e98', fontSize: 11 },
          min: 0,
          max: 100,
          axisLine: { show: false },
          axisLabel: { color: '#8b8e98', fontSize: 11, formatter: (v: number) => `${v}%` },
          splitLine: { show: false },
        },
      ],
      series: [
        {
          name: '目标价',
          type: 'line',
          data: targetPrices,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2, color: '#d4a017' },
          itemStyle: { color: '#d4a017' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(212,160,23,0.20)' },
                { offset: 1, color: 'rgba(212,160,23,0.02)' },
              ],
            },
          },
          connectNulls: true,
        },
        {
          name: '置信度',
          type: 'line',
          yAxisIndex: 1,
          data: confidences,
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: { width: 2, color: '#3b82f6' },
          itemStyle: { color: '#3b82f6' },
          connectNulls: true,
        },
      ],
    }
  }, [history])

  /* ── 因素分析条形图配置 ─────────────────────────────── */
  const factorChartOption = useMemo(() => {
    if (!prediction?.factors?.length) return {}
    const sorted = [...prediction.factors].sort((a, b) => a.score - b.score)
    const names = sorted.map((f) => f.name)
    const scores = sorted.map((f) => f.score)
    const colors = sorted.map((f) => (f.score >= 50 ? '#22c55e' : '#ef4444'))
    return {
      backgroundColor: '#1e2130',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(30,33,48,0.95)',
        borderColor: '#2d3040',
        textStyle: { color: '#e4e6eb', fontSize: 12 },
        formatter: (params: Array<{ name: string; value: number }>) => {
          const p = params[0]
          return `${p.name}<br/>评分: ${p.value.toFixed(1)}`
        },
      },
      grid: { left: 140, right: 40, top: 20, bottom: 20 },
      xAxis: {
        type: 'value',
        min: 0,
        max: 100,
        axisLine: { show: false },
        axisLabel: { color: '#8b8e98', fontSize: 11 },
        splitLine: { lineStyle: { color: '#2d3040', type: 'dashed' } },
      },
      yAxis: {
        type: 'category',
        data: names,
        axisLine: { lineStyle: { color: '#2d3040' } },
        axisLabel: { color: '#8b8e98', fontSize: 11, width: 120, overflow: 'truncate' },
      },
      series: [
        {
          type: 'bar',
          data: scores.map((v, i) => ({
            value: v,
            itemStyle: { color: colors[i] },
          })),
          barWidth: 16,
          label: {
            show: true,
            position: 'right',
            color: '#8b8e98',
            fontSize: 11,
            formatter: (p: { value: number }) => p.value.toFixed(1),
          },
        },
      ],
    }
  }, [prediction])

  /* ── 历史表格数据（最近 10 条，倒序） ────────────────── */
  const tableRecords = useMemo(() => {
    return [...history].slice(-10).reverse()
  }, [history])

  return (
    <div className="prediction">
      <div className="prediction__header">
        <div>
          <h1 className="prediction__title">AI 预测分析</h1>
          <p className="prediction__subtitle">
            基于 DeepSeek AI 的智能价格预测与风险评估
            {cacheInfo && (
              <span className="prediction__cache-info">
                {' '}· {isCached ? '📦' : '🤖'} {cacheInfo}
              </span>
            )}
          </p>
        </div>
        <div className="prediction__actions">
          <button
            className="prediction__refresh-btn prediction__refresh-btn--primary"
            onClick={() => handleRefresh(false)}
            disabled={refreshing}
          >
            <span className={refreshing ? 'prediction__refresh-icon--spinning' : ''}>
              ⟳
            </span>
            {refreshing ? '检查中...' : '刷新预测'}
          </button>
          <button
            className="prediction__refresh-btn"
            onClick={() => handleRefresh(true)}
            disabled={refreshing}
            title="强制调用 DeepSeek 重新预测（消耗 token）"
          >
            🤖 AI 重新预测
          </button>
        </div>
      </div>

      {error && (
        <div className="prediction__error">
          <span className="prediction__error-icon">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="prediction__loading">
          <div className="prediction__loading-spinner" />
          <span>正在加载预测数据...</span>
        </div>
      )}

      {!loading && !error && (
        <>
          {!prediction ? (
            <div className="prediction__card prediction__empty-card">
              <div className="prediction__empty-content">
                <h2>暂无预测数据</h2>
                <p>请点击"AI 重新预测"按钮触发 DeepSeek AI 分析</p>
                <button
                  className="prediction__refresh-btn prediction__refresh-btn--primary"
                  onClick={() => handleRefresh(true)}
                  disabled={refreshing}
                >
                  {refreshing ? '预测中...' : '开始 AI 预测'}
                </button>
              </div>
            </div>
          ) : (
            <>
              {/* 预测结果主卡片 */}
              <div className="prediction__card prediction__main-card">
                <div className="prediction__card-header">
                  <h2 className="prediction__card-title">预测结果</h2>
                  <span className="prediction__card-badge">
                    {prediction?.data_range?.prediction_type || '短期预测'}
                    {isCached && ' · 缓存'}
                  </span>
                </div>
                <div className="prediction__main-content">
                  <div className="prediction__direction-section">
                    <span className="prediction__label">预测方向</span>
                    <div className={`prediction__direction ${getDirectionClass(prediction?.score)}`}>
                      <span className="prediction__direction-text">
                        {getDirectionLabel(prediction?.score)}
                      </span>
                      <span className="prediction__direction-arrow">
                        {prediction?.score == null
                          ? '→'
                          : prediction.score >= 70
                            ? '↑'
                            : prediction.score <= 30
                              ? '↓'
                              : '→'}
                      </span>
                    </div>
                    <span className="prediction__conclusion">
                      {prediction?.conclusion || '暂无结论'}
                    </span>
                  </div>

                  <div className="prediction__stats-grid">
                    <div className="prediction__stat-item">
                      <span className="prediction__stat-label">目标价</span>
                      <span className="prediction__stat-value">
                        ${formatNumber(prediction?.data_range?.target_price)}
                      </span>
                    </div>
                    <div className="prediction__stat-item">
                      <span className="prediction__stat-label">置信度</span>
                      <span className="prediction__stat-value">
                        {prediction?.confidence != null
                          ? `${(prediction.confidence * 100).toFixed(0)}%`
                          : '--'}
                      </span>
                    </div>
                    <div className="prediction__stat-item">
                      <span className="prediction__stat-label">预测评分</span>
                      <span className="prediction__stat-value">
                        {formatNumber(prediction?.score, 1)}
                      </span>
                    </div>
                    <div className="prediction__stat-item">
                      <span className="prediction__stat-label">生成时间</span>
                      <span className="prediction__stat-value">
                        {prediction?.generated_at
                          ? new Date(prediction.generated_at).toLocaleString()
                          : '--'}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* 支撑/阻力位 */}
              <div className="prediction__card prediction__levels-card">
                <div className="prediction__card-header">
                  <h2 className="prediction__card-title">关键价位</h2>
                  <span className="prediction__card-badge">支撑/阻力</span>
                </div>
                <div className="prediction__levels-content">
                  <div className="prediction__level-item prediction__level--support">
                    <div className="prediction__level-header">
                      <span className="prediction__level-icon">📉</span>
                      <span className="prediction__level-label">支撑位</span>
                    </div>
                    <div className="prediction__level-value">
                      ${formatNumber(supportLevel)}
                    </div>
                  </div>
                  <div className="prediction__level-item prediction__level--resistance">
                    <div className="prediction__level-header">
                      <span className="prediction__level-icon">📈</span>
                      <span className="prediction__level-label">阻力位</span>
                    </div>
                    <div className="prediction__level-value">
                      ${formatNumber(resistanceLevel)}
                    </div>
                  </div>
                </div>
              </div>

              {/* 历史预测趋势图 */}
              {history.length > 1 && (
                <div className="prediction__card prediction__trend-card">
                  <div className="prediction__card-header">
                    <h2 className="prediction__card-title">历史预测趋势</h2>
                    <span className="prediction__card-badge">近 {history.length} 条记录</span>
                  </div>
                  <ReactECharts
                    option={trendChartOption}
                    style={{ height: 360, width: '100%' }}
                    opts={{ renderer: 'canvas' }}
                    notMerge
                  />
                </div>
              )}

              {/* 因素分析可视化 */}
              {prediction.factors && prediction.factors.length > 0 && (
                <div className="prediction__card prediction__factor-card">
                  <div className="prediction__card-header">
                    <h2 className="prediction__card-title">因素分析</h2>
                    <span className="prediction__card-badge">{prediction.factors.length} 项因素</span>
                  </div>
                  <ReactECharts
                    option={factorChartOption}
                    style={{ height: Math.max(200, prediction.factors.length * 36 + 40), width: '100%' }}
                    opts={{ renderer: 'canvas' }}
                    notMerge
                  />
                </div>
              )}

              {/* 风险因素 */}
              <div className="prediction__card prediction__risk-card">
                <div className="prediction__card-header">
                  <h2 className="prediction__card-title">风险因素</h2>
                  <span className="prediction__card-badge">{riskFactors.length || rawRiskFactors.length} 项</span>
                </div>
                <div className="prediction__risk-content">
                  {riskFactors.length === 0 && rawRiskFactors.length === 0 ? (
                    <p className="prediction__risk-empty">暂无显著风险因素</p>
                  ) : riskFactors.length > 0 ? (
                    <ul className="prediction__risk-list">
                      {riskFactors.map((factor, index) => (
                        <li key={index} className="prediction__risk-item">
                          <div className="prediction__risk-item-header">
                            <span className="prediction__risk-name">{factor.name}</span>
                            <span className="prediction__risk-score">
                              风险评分: {formatNumber(factor.score, 1)}
                            </span>
                          </div>
                          <p className="prediction__risk-evidence">{factor.evidence}</p>
                          <div className="prediction__risk-impact">
                            影响程度: {factor.impact}
                          </div>
                        </li>
                      ))}
                    </ul>
                  ) : (
                    <ul className="prediction__risk-list">
                      {rawRiskFactors.map((risk, index) => (
                        <li key={index} className="prediction__risk-item">
                          <p className="prediction__risk-evidence">{risk}</p>
                        </li>
                      ))}
                    </ul>
                  )}
                </div>
              </div>

              {/* 历史预测记录表格 */}
              {tableRecords.length > 0 && (
                <div className="prediction__card prediction__history-card">
                  <div className="prediction__card-header">
                    <h2 className="prediction__card-title">历史预测记录</h2>
                    <span className="prediction__card-badge">最近 10 条</span>
                  </div>
                  <div className="prediction__table-wrap">
                    <table className="prediction__table">
                      <thead>
                        <tr>
                          <th>日期</th>
                          <th>方向</th>
                          <th>目标价</th>
                          <th>置信度</th>
                          <th>评分</th>
                          <th>来源</th>
                        </tr>
                      </thead>
                      <tbody>
                        {tableRecords.map((r, idx) => (
                          <tr key={r.id ?? idx}>
                            <td>
                              {r.generated_at
                                ? new Date(r.generated_at).toLocaleDateString()
                                : '--'}
                            </td>
                            <td>
                              <span
                                className={`prediction__table-direction ${
                                  r.score >= 70
                                    ? 'prediction__table-direction--bullish'
                                    : r.score <= 30
                                      ? 'prediction__table-direction--bearish'
                                      : 'prediction__table-direction--neutral'
                                }`}
                              >
                                {getDirectionLabel(r.score)}
                              </span>
                            </td>
                            <td>${formatNumber(r.data_range?.target_price)}</td>
                            <td>
                              {r.confidence != null
                                ? `${(r.confidence * 100).toFixed(0)}%`
                                : '--'}
                            </td>
                            <td>{formatNumber(r.score, 1)}</td>
                            <td>
                              <span className="prediction__table-source">
                                {r.source === 'ai' ? '🤖 AI' : '📦 缓存'}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}
    </div>
  )
}
