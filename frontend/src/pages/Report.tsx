import { useCallback, useEffect, useState } from 'react'
import { fetchDailyReport, fetchReportHistory } from '@/services'
import type { DailyReport, ReportHistoryItem } from '@/services'
import './Report.css'

export default function Report() {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const [report, setReport] = useState<DailyReport | null>(null)
  const [history, setHistory] = useState<ReportHistoryItem[]>([])
  const [selectedDate, setSelectedDate] = useState<string>('')
  const [activeHistoryDate, setActiveHistoryDate] = useState<string>('')

  /** 加载每日报告 */
  const loadReport = useCallback(async (date?: string) => {
    try {
      const res = await fetchDailyReport(date || undefined)
      setReport(res.data)
      if (res.data?.date) {
        setActiveHistoryDate(res.data.date)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '报告加载失败')
    }
  }, [])

  /** 加载历史报告列表 */
  const loadHistory = useCallback(async () => {
    try {
      const res = await fetchReportHistory(7)
      setHistory(res.data.reports || [])
    } catch (err) {
      console.error('历史报告加载失败:', err)
    }
  }, [])

  /** 初始化 */
  useEffect(() => {
    async function init() {
      setLoading(true)
      await Promise.all([loadReport(), loadHistory()])
      setLoading(false)
    }
    init()
  }, [loadReport, loadHistory])

  /** 刷新 */
  const handleRefresh = async () => {
    setRefreshing(true)
    setError(null)
    await Promise.all([loadReport(selectedDate || undefined), loadHistory()])
    setRefreshing(false)
  }

  /** 日期切换 */
  const handleDateChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const date = e.target.value
    setSelectedDate(date)
    loadReport(date)
  }

  /** 点击历史报告 */
  const handleHistoryClick = (date: string) => {
    setSelectedDate(date)
    setActiveHistoryDate(date)
    loadReport(date)
  }

  /** 格式化数字 */
  const formatNumber = (value: number | null | undefined, decimals = 2) => {
    if (value == null || isNaN(value)) return '--'
    return value.toFixed(decimals)
  }

  /** 获取评分样式类名 */
  const getScoreClass = (score: number | null | undefined) => {
    if (score == null) return ''
    return score >= 0 ? 'report__analysis-stat-value--positive' : 'report__analysis-stat-value--negative'
  }

  /** 格式化置信度 */
  const formatConfidence = (value: number | null | undefined) => {
    if (value == null || isNaN(value)) return '--'
    return `${(value * 100).toFixed(0)}%`
  }

  const snapshot = report?.market_snapshot
  const analysis = report?.analysis_summary

  return (
    <div className="report">
      {/* 页面头部 */}
      <div className="report__header">
        <div>
          <h1 className="report__title">每日研究报告</h1>
          <p className="report__subtitle">
            跨市场综合分析 · AI 智能预测
            {report?.generated_at && (
              <span> · 生成于 {new Date(report.generated_at).toLocaleString('zh-CN')}</span>
            )}
          </p>
        </div>
        <div className="report__header-actions">
          <input
            type="date"
            className="report__date-picker"
            value={selectedDate}
            onChange={handleDateChange}
            title="选择日期查看历史报告"
          />
          <button
            className="report__refresh-btn"
            onClick={handleRefresh}
            disabled={refreshing}
            title="刷新报告数据"
          >
            <span className={`report__refresh-icon ${refreshing ? 'spinning' : ''}`}>↻</span>
            {refreshing ? '刷新中...' : '刷新'}
          </button>
        </div>
      </div>

      {/* 错误提示 */}
      {error && (
        <div className="report__error">
          <span>⚠</span>
          <span>{error}</span>
          <button className="report__error-close" onClick={() => setError(null)}>×</button>
        </div>
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="report__loading">
          <div className="report__loading-spinner" />
          <span>正在加载报告数据...</span>
        </div>
      )}

      {!loading && report && (
        <>
          {/* 市场快照 - 指标卡片网格 */}
          <div className="report__card">
            <div className="report__card-header">
              <h2 className="report__card-title">市场快照</h2>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span className="report__card-badge">{report.date}</span>
                {report._cached && <span className="report__cached-badge">缓存</span>}
              </div>
            </div>
            <div className="report__grid">
              {/* 黄金价格 */}
              <div className="report__indicator-card">
                <div className="report__indicator-header">
                  <h3 className="report__indicator-title">黄金价格</h3>
                  <span className="report__indicator-symbol">XAU</span>
                </div>
                <div className="report__indicator-value">
                  ${formatNumber(snapshot?.gold?.price)}
                </div>
                <div className="report__indicator-extra">
                  {snapshot?.gold?.unit || 'USD/oz'} · {snapshot?.gold?.date || '--'}
                </div>
              </div>

              {/* 白银价格 */}
              <div className="report__indicator-card">
                <div className="report__indicator-header">
                  <h3 className="report__indicator-title">白银价格</h3>
                  <span className="report__indicator-symbol">XAG</span>
                </div>
                <div className="report__indicator-value">
                  ${formatNumber(snapshot?.silver?.price)}
                </div>
                <div className="report__indicator-extra">
                  {snapshot?.silver?.unit || 'USD/oz'} · {snapshot?.silver?.date || '--'}
                </div>
              </div>

              {/* 金银比 */}
              <div className="report__indicator-card report__ratio-card">
                <div className="report__indicator-header">
                  <h3 className="report__indicator-title">金银比</h3>
                  <span className="report__indicator-symbol">GSR</span>
                </div>
                <div className="report__indicator-value">
                  {formatNumber(snapshot?.gold_silver_ratio, 1)}
                </div>
                <div className="report__indicator-extra">
                  黄金/白银价格比率
                </div>
              </div>

              {/* 美元指数（EUR 汇率） */}
              <div className="report__indicator-card">
                <div className="report__indicator-header">
                  <h3 className="report__indicator-title">美元汇率</h3>
                  <span className="report__indicator-symbol">USD</span>
                </div>
                <div className="report__indicator-value">
                  EUR {formatNumber(snapshot?.usd_rates?.EUR, 4)}
                </div>
                <div className="report__indicator-extra">
                  JPY {formatNumber(snapshot?.usd_rates?.JPY, 2)} · CNY {formatNumber(snapshot?.usd_rates?.CNY, 4)}
                </div>
              </div>

              {/* 10Y 美债 */}
              <div className="report__indicator-card">
                <div className="report__indicator-header">
                  <h3 className="report__indicator-title">10Y 美债收益率</h3>
                  <span className="report__indicator-symbol">US10Y</span>
                </div>
                <div className="report__indicator-value">
                  {formatNumber(snapshot?.treasury_10y?.value, 3)}%
                </div>
                <div className="report__indicator-extra">
                  {snapshot?.treasury_10y?.date || '--'}
                </div>
              </div>

              {/* WTI 原油 */}
              <div className="report__indicator-card">
                <div className="report__indicator-header">
                  <h3 className="report__indicator-title">WTI 原油</h3>
                  <span className="report__indicator-symbol">WTI</span>
                </div>
                <div className="report__indicator-value">
                  ${formatNumber(snapshot?.wti_oil?.price)}
                </div>
                <div className="report__indicator-extra">
                  {snapshot?.wti_oil?.unit || 'USD/bbl'} · {snapshot?.wti_oil?.date || '--'}
                </div>
              </div>

              {/* S&P 500 */}
              <div className="report__indicator-card">
                <div className="report__indicator-header">
                  <h3 className="report__indicator-title">S&P 500</h3>
                  <span className="report__indicator-symbol">SPX</span>
                </div>
                <div className="report__indicator-value">
                  {formatNumber(snapshot?.sp500?.value, 0)}
                </div>
                <div className="report__indicator-extra">
                  {snapshot?.sp500?.date || '--'}
                </div>
              </div>

              {/* 联邦基金利率 */}
              <div className="report__indicator-card">
                <div className="report__indicator-header">
                  <h3 className="report__indicator-title">联邦基金利率</h3>
                  <span className="report__indicator-symbol">FED</span>
                </div>
                <div className="report__indicator-value">
                  {formatNumber(snapshot?.fed_rate?.value, 2)}%
                </div>
                <div className="report__indicator-extra">
                  {snapshot?.fed_rate?.date || '--'}
                </div>
              </div>

              {/* VIX 恐慌指数 */}
              <div className="report__indicator-card">
                <div className="report__indicator-header">
                  <h3 className="report__indicator-title">VIX 恐慌指数</h3>
                  <span className="report__indicator-symbol">VIX</span>
                </div>
                <div className="report__indicator-value">
                  {formatNumber(snapshot?.vix?.value, 2)}
                </div>
                <div className="report__indicator-extra">
                  {snapshot?.vix?.date || '--'}
                </div>
              </div>
            </div>
          </div>

          {/* 分析摘要区域 */}
          <div className="report__card">
            <div className="report__card-header">
              <h2 className="report__card-title">分析摘要</h2>
              <span className="report__card-badge">综合分析</span>
            </div>
            <div className="report__analysis-grid">
              {/* 跨市场分析 */}
              <div className="report__analysis-column report__analysis-column--market">
                <h3 className="report__analysis-type">跨市场分析</h3>
                <p className="report__analysis-conclusion">
                  {analysis?.market?.conclusion || '暂无分析结论'}
                </p>
                <div className="report__analysis-stats">
                  <div className="report__analysis-stat">
                    <span className="report__analysis-stat-label">评分</span>
                    <span className={`report__analysis-stat-value ${getScoreClass(analysis?.market?.score)}`}>
                      {formatNumber(analysis?.market?.score, 1)}
                    </span>
                  </div>
                  <div className="report__analysis-stat">
                    <span className="report__analysis-stat-label">置信度</span>
                    <span className="report__analysis-stat-value">
                      {formatConfidence(analysis?.market?.confidence)}
                    </span>
                  </div>
                </div>
              </div>

              {/* 宏观分析 */}
              <div className="report__analysis-column report__analysis-column--macro">
                <h3 className="report__analysis-type">宏观分析</h3>
                <p className="report__analysis-conclusion">
                  {analysis?.macro?.conclusion || '暂无分析结论'}
                </p>
                <div className="report__analysis-stats">
                  <div className="report__analysis-stat">
                    <span className="report__analysis-stat-label">评分</span>
                    <span className={`report__analysis-stat-value ${getScoreClass(analysis?.macro?.score)}`}>
                      {formatNumber(analysis?.macro?.score, 1)}
                    </span>
                  </div>
                  <div className="report__analysis-stat">
                    <span className="report__analysis-stat-label">置信度</span>
                    <span className="report__analysis-stat-value">
                      {formatConfidence(analysis?.macro?.confidence)}
                    </span>
                  </div>
                </div>
              </div>

              {/* AI 预测 */}
              <div className="report__analysis-column report__analysis-column--ai">
                <h3 className="report__analysis-type">AI 预测</h3>
                <p className="report__analysis-conclusion">
                  {analysis?.ai_prediction?.conclusion || '暂无分析结论'}
                </p>
                <div className="report__analysis-stats">
                  <div className="report__analysis-stat">
                    <span className="report__analysis-stat-label">评分</span>
                    <span className={`report__analysis-stat-value ${getScoreClass(analysis?.ai_prediction?.score)}`}>
                      {formatNumber(analysis?.ai_prediction?.score, 1)}
                    </span>
                  </div>
                  <div className="report__analysis-stat">
                    <span className="report__analysis-stat-label">置信度</span>
                    <span className="report__analysis-stat-value">
                      {formatConfidence(analysis?.ai_prediction?.confidence)}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* 历史报告列表 */}
          <div className="report__card report__history-card">
            <div className="report__card-header">
              <h2 className="report__card-title">历史报告</h2>
              <span className="report__card-badge">最近 7 天</span>
            </div>
            {history.length > 0 ? (
              <div className="report__history-list">
                {history.map((item) => (
                  <div
                    key={item.date}
                    className={`report__history-item ${activeHistoryDate === item.date ? 'report__history-item--active' : ''}`}
                    onClick={() => handleHistoryClick(item.date)}
                  >
                    <span className="report__history-date">{item.date}</span>
                    <span className="report__history-gold">
                      {item.gold_price != null ? `$${formatNumber(item.gold_price)}` : '--'}
                    </span>
                    <span className="report__history-conclusion">
                      {item.ai_conclusion || '--'}
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <div className="report__history-empty">
                <span className="report__history-empty-icon">📊</span>
                <span>暂无历史报告数据</span>
                <span style={{ fontSize: 12 }}>刷新页面或等待系统自动生成报告</span>
              </div>
            )}
          </div>
        </>
      )}

      {!loading && !report && !error && (
        <div className="report__loading">
          <span>暂无报告数据</span>
        </div>
      )}
    </div>
  )
}
