import { useEffect, useState } from 'react'
import {
  fetchGoldPrediction,
  triggerGoldPrediction,
  triggerAISummary,
} from '@/services'
import type { PredictionResult, AISummary } from '@/types'
import './Prediction.css'

export default function Prediction() {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [prediction, setPrediction] = useState<PredictionResult | null>(null)
  const [aiSummary, setAiSummary] = useState<AISummary | null>(null)

  // 加载数据
  useEffect(() => {
    loadData()
  }, [])

  async function loadData() {
    try {
      setLoading(true)
      setError(null)

      const [predictRes, summaryRes] = await Promise.all([
        fetchGoldPrediction(1),
        triggerAISummary(),
      ])

      if (predictRes.data.records.length > 0) {
        setPrediction(predictRes.data.records[0])
      }
      setAiSummary(summaryRes.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '数据加载失败')
    } finally {
      setLoading(false)
    }
  }

  // 刷新预测
  async function handleRefresh() {
    try {
      setRefreshing(true)
      setError(null)

      const result = await triggerGoldPrediction()
      setPrediction(result.data)

      // 同时刷新摘要
      const summaryRes = await triggerAISummary()
      setAiSummary(summaryRes.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '预测触发失败')
    } finally {
      setRefreshing(false)
    }
  }

  // 格式化数字
  const formatNumber = (value: number | null | undefined, decimals = 2) => {
    if (value == null) return '--'
    return value.toFixed(decimals)
  }

  // 获取方向标签
  const getDirectionLabel = (score: number | null | undefined) => {
    if (score == null) return '--'
    if (score >= 70) return '看涨'
    if (score <= 30) return '看跌'
    return '震荡'
  }

  // 获取方向类名
  const getDirectionClass = (score: number | null | undefined) => {
    if (score == null) return 'prediction__direction--neutral'
    if (score >= 70) return 'prediction__direction--bullish'
    if (score <= 30) return 'prediction__direction--bearish'
    return 'prediction__direction--neutral'
  }

  // 提取支撑/阻力位（从 metadata 或 factors 中）
  const supportLevel = prediction?.metadata?.support_level as number | undefined
  const resistanceLevel = prediction?.metadata?.resistance_level as number | undefined

  // 提取风险因素
  const riskFactors = prediction?.factors?.filter((f) => f.score < 50) || []

  return (
    <div className="prediction">
      <div className="prediction__header">
        <div>
          <h1 className="prediction__title">AI 预测分析</h1>
          <p className="prediction__subtitle">
            基于 DeepSeek AI 的智能价格预测与风险评估
          </p>
        </div>
        <button
          className="prediction__refresh-btn"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <span className={refreshing ? 'prediction__refresh-icon--spinning' : ''}>
            ⟳
          </span>
          {refreshing ? '预测中...' : '刷新预测'}
        </button>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="prediction__error">
          <span className="prediction__error-icon">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="prediction__loading">
          <div className="prediction__loading-spinner" />
          <span>正在加载预测数据...</span>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* AI 行情摘要 */}
          {aiSummary && (
            <div className="prediction__card prediction__summary-card">
              <div className="prediction__card-header">
                <h2 className="prediction__card-title">AI 行情摘要</h2>
                <span className="prediction__card-badge">DeepSeek AI</span>
              </div>
              <div className="prediction__summary-content">
                <p className="prediction__summary-text">
                  {aiSummary.summary || '暂无摘要'}
                </p>
                {aiSummary.context && (
                  <p className="prediction__summary-context">{aiSummary.context}</p>
                )}
              </div>
            </div>
          )}

          {/* 预测结果主卡片 */}
          <div className="prediction__card prediction__main-card">
            <div className="prediction__card-header">
              <h2 className="prediction__card-title">预测结果</h2>
              <span className="prediction__card-badge">
                {prediction?.data_range?.prediction_type || '短期预测'}
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
                  <span className="prediction__stat-label">时间范围</span>
                  <span className="prediction__stat-value">
                    {prediction?.data_range?.time_horizon || '--'}
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

          {/* 风险因素 */}
          <div className="prediction__card prediction__risk-card">
            <div className="prediction__card-header">
              <h2 className="prediction__card-title">风险因素</h2>
              <span className="prediction__card-badge">{riskFactors.length} 项</span>
            </div>
            <div className="prediction__risk-content">
              {riskFactors.length === 0 ? (
                <p className="prediction__risk-empty">暂无显著风险因素</p>
              ) : (
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
              )}
            </div>
          </div>
        </>
      )}
    </div>
  )
}
