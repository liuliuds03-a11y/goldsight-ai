import { useCallback, useEffect, useState } from 'react'
import { get } from '@/services'
import './News.css'

interface NewsArticle {
  title: string
  link: string
  description: string
  source: string
  category: string
  icon: string
  pub_date: string | null
  published_at: string | null
}

interface NewsData {
  articles: NewsArticle[]
  total: number
  sources: string[]
  categories: string[]
  _cached: boolean
  updated_at: string
}

export default function News() {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [newsData, setNewsData] = useState<NewsData | null>(null)
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [selectedSource, setSelectedSource] = useState<string>('all')

  const loadNews = useCallback(async (forceRefresh = false) => {
    try {
      if (forceRefresh) {
        setRefreshing(true)
      } else {
        setLoading(true)
      }
      setError(null)

      const params: Record<string, unknown> = { limit: 50 }
      if (selectedCategory !== 'all') params.category = selectedCategory
      if (selectedSource !== 'all') params.source = selectedSource

      const res = await get<NewsData>('/news/feed', params)
      setNewsData(res.data)
    } catch (err) {
      setError(err instanceof Error ? err.message : '新闻加载失败')
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }, [selectedCategory, selectedSource])

  useEffect(() => {
    loadNews()
  }, [loadNews])

  const handleRefresh = async () => {
    // 清除缓存并重新获取
    try {
      await get('/news/feed', { limit: 50, _refresh: true })
    } catch {}
    await loadNews(true)
  }

  const formatTime = (dateStr: string | null) => {
    if (!dateStr) return '未知时间'
    try {
      const date = new Date(dateStr)
      const now = new Date()
      const diff = now.getTime() - date.getTime()
      const hours = Math.floor(diff / 3600000)
      const days = Math.floor(diff / 86400000)

      if (hours < 1) return '刚刚'
      if (hours < 24) return `${hours}小时前`
      if (days < 7) return `${days}天前`
      return date.toLocaleDateString('zh-CN')
    } catch {
      return dateStr
    }
  }

  const openLink = (url: string) => {
    if (url) window.open(url, '_blank', 'noopener,noreferrer')
  }

  return (
    <div className="news">
      {/* 页面头部 */}
      <div className="news__header">
        <div>
          <h1 className="news__title">新闻资讯</h1>
          <p className="news__subtitle">
            全球黄金及贵金属市场新闻 · 宏观经济动态 · 地缘政治事件
            {newsData?.updated_at && (
              <span className="news__update-time">
                · 更新于 {new Date(newsData.updated_at).toLocaleTimeString('zh-CN')}
              </span>
            )}
          </p>
        </div>
        <button
          className="news__refresh-btn"
          onClick={handleRefresh}
          disabled={refreshing}
        >
          <span className={refreshing ? 'news__refresh-icon--spinning' : ''}>↻</span>
          {refreshing ? '刷新中' : '刷新'}
        </button>
      </div>

      {/* 筛选栏 */}
      {newsData && (
        <div className="news__filters">
          <div className="news__filter-group">
            <span className="news__filter-label">分类：</span>
            <div className="news__filter-buttons">
              <button
                className={`news__filter-btn ${selectedCategory === 'all' ? 'active' : ''}`}
                onClick={() => setSelectedCategory('all')}
              >
                全部
              </button>
              {newsData.categories.map((cat) => (
                <button
                  key={cat}
                  className={`news__filter-btn ${selectedCategory === cat ? 'active' : ''}`}
                  onClick={() => setSelectedCategory(cat)}
                >
                  {cat}
                </button>
              ))}
            </div>
          </div>
          <div className="news__filter-group">
            <span className="news__filter-label">来源：</span>
            <div className="news__filter-buttons">
              <button
                className={`news__filter-btn ${selectedSource === 'all' ? 'active' : ''}`}
                onClick={() => setSelectedSource('all')}
              >
                全部
              </button>
              {newsData.sources.map((src) => (
                <button
                  key={src}
                  className={`news__filter-btn ${selectedSource === src ? 'active' : ''}`}
                  onClick={() => setSelectedSource(src)}
                >
                  {src}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="news__error">
          <span className="news__error-icon">⚠</span>
          <span>{error}</span>
          <button className="news__error-retry" onClick={() => loadNews()}>重试</button>
        </div>
      )}

      {/* 加载状态 */}
      {loading && (
        <div className="news__loading">
          <div className="news__loading-spinner" />
          <span>正在加载新闻...</span>
        </div>
      )}

      {/* 新闻列表 */}
      {!loading && !error && newsData && (
        <div className="news__content">
          {newsData.articles.length === 0 ? (
            <div className="news__empty">
              <span className="news__empty-icon">📰</span>
              <p>暂无相关新闻</p>
              <p className="news__empty-hint">请尝试调整筛选条件或刷新页面</p>
            </div>
          ) : (
            <div className="news__grid">
              {newsData.articles.map((article, idx) => (
                <article
                  key={`${article.source}-${idx}`}
                  className="news__card"
                  onClick={() => openLink(article.link)}
                >
                  <div className="news__card-header">
                    <span className="news__card-category">
                      {article.icon && <span className="news__card-icon">{article.icon}</span>}
                      {article.category}
                    </span>
                    <span className="news__card-source">{article.source}</span>
                  </div>
                  <h3 className="news__card-title">{article.title}</h3>
                  {article.description && (
                    <p className="news__card-desc">{article.description}</p>
                  )}
                  <div className="news__card-footer">
                    <span className="news__card-time">
                      {formatTime(article.pub_date || article.published_at)}
                    </span>
                    <span className="news__card-link">阅读全文 →</span>
                  </div>
                </article>
              ))}
            </div>
          )}

          {/* 统计信息 */}
          <div className="news__stats">
            <span>共 {newsData.total} 条新闻</span>
            {newsData._cached && <span className="news__cached-badge">缓存数据</span>}
          </div>
        </div>
      )}
    </div>
  )
}
