import { useCallback, useEffect, useState, useMemo } from 'react'
import ReactECharts from 'echarts-for-react'
import { fetchPreciousMetals, fetchRealtimeAll, refreshRealtime } from '@/services'
import type { RealtimeAll } from '@/services'
import type { PreciousMetalRecord } from '@/types'
import './Silver.css'

/** 白银基本面静态数据 */
const FUNDAMENTALS = [
  {
    icon: '️',
    title: '矿产供应',
    items: [
      '全球白银年产量约 2.6 万吨',
      '主要产银国：墨西哥、秘鲁、中国',
      '约 70% 白银来自伴生矿（铅锌铜矿）',
      '供给弹性较低，受主金属价格影响大',
    ],
  },
  {
    icon: '',
    title: '工业需求',
    items: [
      '光伏产业为最大工业需求来源（占 20%+）',
      '电子电器、焊接材料、催化剂',
      '5G 基站与新能源汽车推动增量需求',
      '工业需求占总需求约 50%',
    ],
  },
  {
    icon: '📊',
    title: '供需格局',
    items: [
      '全球白银连续四年出现结构性供给短缺',
      '2024 年供需缺口约 2,150 吨',
      '地上库存持续下降至历史低位',
      '投资需求（银条银币）波动较大',
    ],
  },
  {
    icon: '💍',
    title: '投资与饰品',
    items: [
      '银饰及银器需求约占 15%',
      '白银兼具贵金属与工业金属双重属性',
      '散户投资重要渠道：ETF、实物银条',
      '投机性较强，价格波动率高于黄金',
    ],
  },
]

export default function Silver() {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [prices, setPrices] = useState<PreciousMetalRecord[]>([])
  const [realtimeSilver, setRealtimeSilver] = useState<RealtimeAll['silver']>(null)
  const [realtimeGold, setRealtimeGold] = useState<RealtimeAll['gold'] | null>(null)

  const loadData = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const [priceRes, realtimeRes] = await Promise.all([
        fetchPreciousMetals({ metal: 'silver', limit: 120 }),
        fetchRealtimeAll(),
      ])

      const priceRecords = priceRes.data.records
      priceRecords.sort(
        (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
      )
      setPrices(priceRecords)

      const rt = realtimeRes.data
      setRealtimeSilver(rt.silver)
      setRealtimeGold(rt.gold)
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
      await refreshRealtime()
      await loadData()
    } catch (err) {
      setError(err instanceof Error ? err.message : '刷新失败')
    } finally {
      setRefreshing(false)
    }
  }

  /* ── 金银比 ─────────────────────────────────────── */
  const goldSilverRatio = useMemo(() => {
    if (realtimeGold?.price && realtimeSilver?.price) {
      return (realtimeGold.price / realtimeSilver.price).toFixed(1)
    }
    return null
  }, [realtimeGold, realtimeSilver])

  /** 金银比区间解读 */
  const ratioInterpretation = useMemo(() => {
    if (!goldSilverRatio) return null
    const ratio = parseFloat(goldSilverRatio)
    if (ratio < 60) return { level: '偏低', desc: '白银相对强势，可能存在补涨动能', cls: 'low' }
    if (ratio < 80) return { level: '中性', desc: '金银价格处于历史均衡区间', cls: 'mid' }
    return { level: '偏高', desc: '白银相对弱势，历史上此区间往往预示白银补涨', cls: 'high' }
  }, [goldSilverRatio])

  /* ── 图表配置 ──────────────────────────────────────── */
  const chartOption = useMemo(() => {
    if (prices.length === 0) return {}

    const dates = prices.map((p) => p.timestamp.slice(0, 10))
    const closePrices = prices.map((p) => p.close)

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
        data: ['收盘价'],
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
          fillerColor: 'rgba(192,192,192,0.15)',
          handleStyle: { color: '#c0c0c0' },
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
          formatter: (v: number) => v.toFixed(2),
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
          lineStyle: { width: 2, color: '#c0c0c0' },
          areaStyle: {
            color: {
              type: 'linear',
              x: 0, y: 0, x2: 0, y2: 1,
              colorStops: [
                { offset: 0, color: 'rgba(192,192,192,0.25)' },
                { offset: 1, color: 'rgba(192,192,192,0.02)' },
              ],
            },
          },
          itemStyle: { color: '#c0c0c0' },
        },
      ],
    }
  }, [prices])

  const tableRecords = useMemo(() => {
    return [...prices].slice(-10).reverse()
  }, [prices])

  const fmt = (v: number | null | undefined, d = 2) =>
    v != null ? v.toFixed(d) : '--'

  const changeClass = (v: number | null | undefined) => {
    if (v == null) return 'silver__table-change--neutral'
    return v >= 0 ? 'silver__table-change--up' : 'silver__table-change--down'
  }

  const changeSign = (v: number | null | undefined) => {
    if (v == null) return ''
    return v >= 0 ? '+' : ''
  }

  return (
    <div className="silver">
      {/* 实时价格头部 */}
      <div className="silver__realtime-header">
        <div className="silver__realtime-info">
          <h1 className="silver__title">白银详情</h1>
          <p className="silver__subtitle">XAG/USD 行情走势与基本面分析</p>
        </div>
        <div className="silver__realtime-cards">
          {/* 实时银价 */}
          <div className="silver__realtime-card silver__realtime-card--silver">
            <span className="silver__realtime-label">实时银价</span>
            <span className="silver__realtime-value">
              ${realtimeSilver?.price ? fmt(realtimeSilver.price) : '--'}
            </span>
            <span className="silver__realtime-meta">
              {realtimeSilver?.date || '--'} · {fmt(realtimeSilver?.price_per_gram_usd)}/克
            </span>
          </div>
          {/* 实时金价（参考） */}
          <div className="silver__realtime-card silver__realtime-card--gold">
            <span className="silver__realtime-label">实时金价</span>
            <span className="silver__realtime-value">
              ${realtimeGold?.price ? fmt(realtimeGold.price) : '--'}
            </span>
            <span className="silver__realtime-meta">XAU/USD</span>
          </div>
          {/* 金银比 */}
          {goldSilverRatio && (
            <div className="silver__realtime-card silver__realtime-card--ratio">
              <span className="silver__realtime-label">金银比</span>
              <span className="silver__realtime-value">{goldSilverRatio}</span>
              <span className="silver__realtime-meta">Gold/Silver</span>
            </div>
          )}
          {/* 刷新按钮 */}
          <button
            className="silver__refresh-btn"
            onClick={handleRefresh}
            disabled={refreshing}
            title="刷新所有数据"
          >
            <span className={refreshing ? 'silver__refresh-icon--spinning' : ''}>↻</span>
            {refreshing ? '刷新中' : '刷新'}
          </button>
        </div>
      </div>

      {error && (
        <div className="silver__error">
          <span className="silver__error-icon">⚠</span>
          <span>{error}</span>
        </div>
      )}

      {loading && (
        <div className="silver__loading">
          <div className="silver__loading-spinner" />
          <span>正在加载数据...</span>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* 价格走势图 */}
          {prices.length > 0 && (
            <section className="silver__card silver__chart-card">
              <div className="silver__card-header">
                <h2 className="silver__card-title">历史价格走势</h2>
                <span className="silver__card-badge">近 120 天</span>
              </div>
              <ReactECharts
                option={chartOption}
                style={{ height: 420, width: '100%' }}
                opts={{ renderer: 'canvas' }}
                notMerge
              />
            </section>
          )}

          {/* 数据表格 */}
          {prices.length > 0 && (
            <section className="silver__card silver__table-card">
              <div className="silver__card-header">
                <h2 className="silver__card-title">最近交易记录</h2>
                <span className="silver__card-badge">最近 10 条</span>
              </div>
              <div className="silver__table-wrap">
                <table className="silver__table">
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
                        <td colSpan={6} className="silver__table-empty">
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
                        <td className={`silver__table-change ${changeClass(r.change_pct)}`}>
                          {changeSign(r.change_pct)}
                          {fmt(r.change_pct)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {/* 白银基本面信息 */}
          <section className="silver__card">
            <div className="silver__card-header">
              <h2 className="silver__card-title">白银基本面概览</h2>
              <span className="silver__card-badge">供需 · 工业 · 投资</span>
            </div>
            <div className="silver__fundamentals-grid">
              {FUNDAMENTALS.map((block) => (
                <div key={block.title} className="silver__info-block">
                  <span className="silver__info-icon">{block.icon}</span>
                  <h3 className="silver__info-title">{block.title}</h3>
                  <ul className="silver__info-list">
                    {block.items.map((item, idx) => (
                      <li key={idx}>{item}</li>
                    ))}
                  </ul>
                </div>
              ))}
            </div>
          </section>

          {/* 金银比历史走势说明 */}
          <section className="silver__card silver__ratio-card">
            <div className="silver__card-header">
              <h2 className="silver__card-title">金银比分析</h2>
              <span className="silver__card-badge">Gold/Silver Ratio</span>
            </div>
            <div className="silver__ratio-content">
              <div className="silver__ratio-current">
                <span className="silver__ratio-number">
                  {goldSilverRatio ?? '--'}
                </span>
                {ratioInterpretation && (
                  <span className="silver__ratio-label">
                    当前区间：{ratioInterpretation.level}
                  </span>
                )}
              </div>

              {/* 区间色条 */}
              <div className="silver__ratio-scale">
                <div className="silver__ratio-segment silver__ratio-segment--low" />
                <div className="silver__ratio-segment silver__ratio-segment--mid" />
                <div className="silver__ratio-segment silver__ratio-segment--high" />
              </div>
              <div className="silver__ratio-legend">
                <span className="silver__ratio-legend-item">
                  <span className="silver__ratio-legend-dot silver__ratio-legend-dot--low" />
                  &lt;60 白银强势
                </span>
                <span className="silver__ratio-legend-item">
                  <span className="silver__ratio-legend-dot silver__ratio-legend-dot--mid" />
                  60-80 均衡
                </span>
                <span className="silver__ratio-legend-item">
                  <span className="silver__ratio-legend-dot silver__ratio-legend-dot--high" />
                  &gt;80 白银弱势
                </span>
              </div>

              {ratioInterpretation && (
                <p className="silver__ratio-desc">
                  {ratioInterpretation.desc}
                </p>
              )}

              <p className="silver__ratio-desc">
                金银比是衡量黄金与白银相对价格的重要指标。历史均值约为 60-70，
                当比值高于 80 时，通常意味着白银被低估，存在均值回归的补涨预期；
                当比值低于 60 时，白银相对黄金表现强势。该指标常被用作白银投资策略的参考依据。
              </p>
            </div>
          </section>
        </>
      )}
    </div>
  )
}
