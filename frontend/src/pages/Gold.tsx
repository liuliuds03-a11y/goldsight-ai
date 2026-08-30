import { useCallback, useEffect, useState, useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { fetchGoldPrices, fetchIndicators, fetchRealtimeAll } from '@/services'
import type { RealtimeAll } from '@/services'
import type {
  GoldPriceRecord,
  TechnicalIndicatorRecord,
} from '@/types'
import './Gold.css'

export default function Gold() {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [prices, setPrices] = useState<GoldPriceRecord[]>([])
  const [indicators, setIndicators] = useState<TechnicalIndicatorRecord[]>([])
  const [realtimeGold, setRealtimeGold] = useState<RealtimeAll['gold'] | null>(null)
  const [realtimeSilver, setRealtimeSilver] = useState<{ price: number; date: string } | null>(null)

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const [priceRes, indicatorRes, realtimeRes] = await Promise.all([
        fetchGoldPrices({ limit: 120 }),
        fetchIndicators({ symbol: 'XAUUSD', indicator: 'MA', limit: 500 }),
        fetchRealtimeAll(),
      ])

      const priceRecords = priceRes.data.records
      priceRecords.sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      )
      setPrices(priceRecords)
      setIndicators(indicatorRes.data.records)

      // 实时数据
      const rt = realtimeRes.data
      setRealtimeGold(rt.gold)
      if (rt.silver && rt.silver.price) {
        setRealtimeSilver({ price: rt.silver.price, date: rt.silver.date })
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '数据加载失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const handleRefresh = async () => {
    setRefreshing(true)
    setError(null)
    try {
      // 强制刷新实时数据
      const { refreshRealtime } = await import('@/services')
      await refreshRealtime()
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : '刷新失败')
    } finally {
      setRefreshing(false)
    }
  }

  /* ── 金银比 ──────────────────────────────────────── */
  const goldSilverRatio = useMemo(() => {
    if (realtimeGold?.price && realtimeSilver?.price) {
      return (realtimeGold.price / realtimeSilver.price).toFixed(1)
    }
    return null
  }, [realtimeGold, realtimeSilver])

  /* ── 按 period 分组指标数据 ─────────────────────────── */
  const maData = useMemo(() => {
    const map: Record<string, Map<string, number>> = {
      '5': new Map(),
      '20': new Map(),
      '60': new Map(),
    }
    for (const ind of indicators) {
      const period = ind.period ?? ''
      if (map[period]) {
        const dateKey = ind.timestamp.slice(0, 10)
        map[period].set(dateKey, ind.value ?? 0)
      }
    }
    return map
  }, [indicators])

  /* ── 图表配置 ──────────────────────────────────────── */
  const chartOption = useMemo(() => {
    if (prices.length === 0) return {}

    const dates = prices.map((p) => p.timestamp.slice(0, 10))
    const closePrices = prices.map((p) => p.close)

    const buildMaSeries = (period: string, name: string, color: string) => {
      const maMap = maData[period]
      const data = dates.map((d) => (maMap.has(d) ? maMap.get(d) : null))
      return {
        name,
        type: 'line' as const,
        data,
        smooth: true,
        lineStyle: { width: 1.5, color },
        symbol: 'none',
        itemStyle: { color },
        connectNulls: false,
      }
    }

    return {
      backgroundColor: '#1e2130',
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(30,33,48,0.95)',
        borderColor: '#2d3040',
        textStyle: { color: '#e4e6eb', fontSize: 12 },
        axisPointer: { type: 'cross' },
      },
      legend: {
        data: ['收盘价', 'MA5', 'MA20', 'MA60'],
        textStyle: { color: '#8b8e98', fontSize: 12 },
        top: 8,
      },
      grid: { left: 60, right: 40, top: 50, bottom: 70 },
      dataZoom: [
        { type: 'inside', start: 0, end: 100 },
        {
          type: 'slider',
          start: 0,
          end: 100,
          height: 24,
          bottom: 10,
          borderColor: '#2d3040',
          backgroundColor: '#1a1d27',
          fillerColor: 'rgba(212,160,23,0.15)',
          handleStyle: { color: '#d4a017' },
          textStyle: { color: '#8b8e98' },
        },
      ],
      xAxis: {
        type: 'category',
        data: dates,
        axisLine: { lineStyle: { color: '#2d3040' } },
        axisLabel: { color: '#8b8e98', fontSize: 11 },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        scale: true,
        axisLine: { show: false },
        axisLabel: {
          color: '#8b8e98',
          fontSize: 11,
          formatter: (v: number) => v.toFixed(0),
        },
        splitLine: { lineStyle: { color: '#2d3040', type: 'dashed' } },
      },
      series: [
        {
          name: '收盘价',
          type: 'line',
          data: closePrices,
          smooth: true,
          symbol: 'none',
          lineStyle: { width: 2, color: '#d4a017' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(212,160,23,0.25)' },
                { offset: 1, color: 'rgba(212,160,23,0.02)' },
              ],
            },
          },
          itemStyle: { color: '#d4a017' },
        },
        buildMaSeries('5', 'MA5', '#d4a017'),
        buildMaSeries('20', 'MA20', '#3b82f6'),
        buildMaSeries('60', 'MA60', '#a855f7'),
      ],
    }
  }, [prices, maData])

  const tableRecords = useMemo(() => {
    return [...prices].slice(-10).reverse()
  }, [prices])

  const fmt = (v: number | null | undefined, d = 2) =>
    v != null ? v.toFixed(d) : '--'

  const changeClass = (v: number | null | undefined) => {
    if (v == null) return 'gold__table-change--neutral'
    return v >= 0 ? 'gold__table-change--up' : 'gold__table-change--down'
  }

  const changeSign = (v: number | null | undefined) => {
    if (v == null) return ''
    return v >= 0 ? '+' : ''
  }

  return (
    <div className="gold">
      {/* 实时价格头部 */}
      <div className="gold__realtime-header">
        <div className="gold__realtime-info">
          <h1 className="gold__title">黄金详情</h1>
          <p className="gold__subtitle">XAU/USD 行情走势与技术指标分析</p>
        </div>
        <div className="gold__realtime-cards">
          {/* 实时金价 */}
          <div className="gold__realtime-card gold__realtime-card--gold">
            <span className="gold__realtime-label">实时金价</span>
            <span className="gold__realtime-value">
              ${realtimeGold?.price ? fmt(realtimeGold.price) : '--'}
            </span>
            <span className="gold__realtime-meta">
              {realtimeGold?.date || '--'} · {fmt(realtimeGold?.price_per_gram_usd)}/克
            </span>
          </div>
          {/* 实时银价 */}
          <div className="gold__realtime-card gold__realtime-card--silver">
            <span className="gold__realtime-label">实时银价</span>
            <span className="gold__realtime-value">
              ${realtimeSilver?.price ? fmt(realtimeSilver.price) : '--'}
            </span>
            <span className="gold__realtime-meta">XAG/USD</span>
          </div>
          {/* 金银比 */}
          {goldSilverRatio && (
            <div className="gold__realtime-card gold__realtime-card--ratio">
              <span className="gold__realtime-label">金银比</span>
              <span className="gold__realtime-value">{goldSilverRatio}</span>
              <span className="gold__realtime-meta">Gold/Silver</span>
            </div>
          )}
          {/* 刷新按钮 */}
          <button
            className="gold__refresh-btn"
            onClick={handleRefresh}
            disabled={refreshing}
            title="刷新所有数据"
          >
            <span className={refreshing ? 'gold__refresh-icon--spinning' : ''}>↻</span>
            {refreshing ? '刷新中' : '刷新'}
          </button>
        </div>
      </div>

      {error && (
        <div className="gold__error">
          <span className="gold__error-icon">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="gold__loading">
          <div className="gold__loading-spinner" />
          <span>正在加载数据...</span>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* 价格走势图 */}
          <section className="gold__card gold__chart-card">
            <div className="gold__card-header">
              <h2 className="gold__card-title">历史价格走势</h2>
              <span className="gold__card-badge">近 120 天</span>
            </div>
            <ReactECharts
              option={chartOption}
              style={{ height: 420, width: '100%' }}
              opts={{ renderer: 'canvas' }}
              notMerge
            />
          </section>

          {/* 数据表格 */}
          <section className="gold__card gold__table-card">
            <div className="gold__card-header">
              <h2 className="gold__card-title">最近交易记录</h2>
              <span className="gold__card-badge">最近 10 条</span>
            </div>
            <div className="gold__table-wrap">
              <table className="gold__table">
                <thead>
                  <tr>
                    <th>日期</th>
                    <th>开盘价</th>
                    <th>最高价</th>
                    <th>最低价</th>
                    <th>收盘价</th>
                    <th>涨跌幅</th>
                  </tr>
                </thead>
                <tbody>
                  {tableRecords.length === 0 && (
                    <tr>
                      <td colSpan={6} className="gold__table-empty">
                        暂无数据
                      </td>
                    </tr>
                  )}
                  {tableRecords.map((r) => (
                    <tr key={r.id}>
                      <td>{r.timestamp.slice(0, 10)}</td>
                      <td>${fmt(r.open)}</td>
                      <td>${fmt(r.high)}</td>
                      <td>${fmt(r.low)}</td>
                      <td>${fmt(r.close)}</td>
                      <td className={`gold__table-change ${changeClass(r.change_pct)}`}>
                        {changeSign(r.change_pct)}
                        {fmt(r.change_pct)}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
