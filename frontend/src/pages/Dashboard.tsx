import { useEffect, useState } from 'react'
import { fetchHealth } from '@/services'
import type { HealthData } from '@/types'
import './Dashboard.css'

type ConnectionStatus = 'checking' | 'connected' | 'disconnected'

export default function Dashboard() {
  const [status, setStatus] = useState<ConnectionStatus>('checking')
  const [healthData, setHealthData] = useState<HealthData | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await fetchHealth()
        setHealthData(res.data)
        setStatus('connected')
      } catch (err) {
        setError(err instanceof Error ? err.message : '连接失败')
        setStatus('disconnected')
      }
    }
    checkHealth()
  }, [])

  return (
    <div className="dashboard">
      <h1 className="dashboard__title">GoldSight AI Dashboard</h1>
      <p className="dashboard__subtitle">全球多金属智能监测与分析平台</p>

      {/* 后端连接状态卡片 */}
      <div className="dashboard__card">
        <h2 className="dashboard__card-title">系统状态</h2>
        <div className="dashboard__status">
          <span
            className={`dashboard__status-dot dashboard__status-dot--${status}`}
          />
          <span className="dashboard__status-text">
            {status === 'checking' && '正在检测后端连接...'}
            {status === 'connected' &&
              `后端服务正常 — ${healthData?.service} (${healthData?.status})`}
            {status === 'disconnected' && `后端连接失败: ${error}`}
          </span>
        </div>
      </div>

      {/* 功能模块占位卡片 */}
      <div className="dashboard__grid">
        <div className="dashboard__module-card">
          <h3>实时行情</h3>
          <p>黄金及多金属实时价格监测</p>
          <span className="dashboard__module-badge">即将上线</span>
        </div>
        <div className="dashboard__module-card">
          <h3>技术指标</h3>
          <p>K线 / MA / RSI / MACD / 布林带</p>
          <span className="dashboard__module-badge">即将上线</span>
        </div>
        <div className="dashboard__module-card">
          <h3>AI 预测</h3>
          <p>短期/长期价格趋势预测</p>
          <span className="dashboard__module-badge">即将上线</span>
        </div>
        <div className="dashboard__module-card">
          <h3>研究报告</h3>
          <p>DeepSeek 综合分析报告</p>
          <span className="dashboard__module-badge">即将上线</span>
        </div>
      </div>
    </div>
  )
}
