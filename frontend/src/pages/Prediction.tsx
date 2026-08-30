import { useEffect, useState } from 'react'
import {
  fetchGoldPrediction,
  triggerGoldPrediction,
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

  // 加载数据：只从数据库读缓存，不调 DeepSeek
  useEffect(() => {
    loadData()
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

  const supportLevel = prediction?.metadata?.support_level as number | undefined
  const resistanceLevel = prediction?.metadata?.resistance_level as number | undefined
  const riskFactors = prediction?.factors?.filter((f) => f.score < 50) || []

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
        </>
      )}
    </div>
  )
}
