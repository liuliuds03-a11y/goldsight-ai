import { get, post } from './client'
import type {
  GoldPriceRecord,
  UsdDataRecord,
  TreasuryYieldRecord,
  OilDataRecord,
  StockMarketRecord,
  TechnicalIndicatorRecord,
  DataQueryResponse,
  DataStats,
} from '@/types'

/** 获取黄金价格数据 */
export function fetchGoldPrices(params?: {
  limit?: number
  offset?: number
  start_date?: string
  end_date?: string
}) {
  return get<DataQueryResponse<GoldPriceRecord>>('/data/gold-prices', params as Record<string, unknown>)
}

/** 获取美元数据 */
export function fetchUsdData(params?: {
  limit?: number
  pair?: string
}) {
  return get<DataQueryResponse<UsdDataRecord>>('/data/usd', params as Record<string, unknown>)
}

/** 获取国债收益率数据 */
export function fetchTreasuryYields(params?: {
  limit?: number
  maturity?: string
}) {
  return get<DataQueryResponse<TreasuryYieldRecord>>('/data/treasury-yields', params as Record<string, unknown>)
}

/** 获取原油数据 */
export function fetchOilData(params?: {
  limit?: number
  oil_type?: string
}) {
  return get<DataQueryResponse<OilDataRecord>>('/data/oil', params as Record<string, unknown>)
}

/** 获取股票市场数据 */
export function fetchStockMarketData(params?: {
  limit?: number
  index_symbol?: string
}) {
  return get<DataQueryResponse<StockMarketRecord>>('/data/stock-market', params as Record<string, unknown>)
}

/** 获取技术指标数据 */
export function fetchIndicators(params?: {
  symbol?: string
  indicator?: string
  category?: string
  limit?: number
  offset?: number
}) {
  return get<DataQueryResponse<TechnicalIndicatorRecord>>('/indicators', params as Record<string, unknown>)
}

/** 触发技术指标计算 */
export function triggerIndicatorCalculation(_symbol = 'XAUUSD') {
  return post<Record<string, unknown>>('/indicators/calculate', null)
}

/** 获取数据统计概览 */
export function fetchDataStats() {
  return get<DataStats>('/data/stats')
}
