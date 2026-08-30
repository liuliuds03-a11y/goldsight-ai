import { get, post } from './client'

/** 实时数据类型 */
export interface RealtimeGold {
  symbol: string
  price: number
  price_per_gram_pln: number
  price_per_gram_usd: number
  pln_usd_rate: number
  date: string
  source: string
  updated_at: string
  _cached: boolean
}

export interface RealtimeUSD {
  base: string
  rates: Record<string, number>
  date: string
  source: string
  updated_at: string
  _cached: boolean
}

export interface RealtimeTreasury {
  symbol: string
  name: string
  value: number
  unit: string
  date: string
  source: string
  updated_at: string
  _cached: boolean
}

export interface RealtimeOil {
  symbol: string
  name: string
  price: number
  unit: string
  date: string
  source: string
  updated_at: string
  _cached: boolean
}

export interface RealtimeStock {
  symbol: string
  name: string
  value: number
  date: string
  source: string
  updated_at: string
  _cached: boolean
}

export interface RealtimeAll {
  gold: RealtimeGold
  usd: RealtimeUSD
  treasury: RealtimeTreasury
  oil: RealtimeOil
  stock: RealtimeStock
  timestamp: string
}

/** 获取所有实时数据 */
export function fetchRealtimeAll() {
  return get<RealtimeAll>('/realtime/all')
}

/** 获取实时黄金价格 */
export function fetchRealtimeGold() {
  return get<RealtimeGold>('/realtime/gold')
}

/** 获取实时美元汇率 */
export function fetchRealtimeUSD() {
  return get<RealtimeUSD>('/realtime/usd')
}

/** 获取实时 10Y 美债收益率 */
export function fetchRealtimeTreasury() {
  return get<RealtimeTreasury>('/realtime/treasury')
}

/** 获取实时原油价格 */
export function fetchRealtimeOil() {
  return get<RealtimeOil>('/realtime/oil')
}

/** 获取实时 S&P 500 */
export function fetchRealtimeStock() {
  return get<RealtimeStock>('/realtime/stock')
}

/** 强制刷新所有实时数据（清除缓存） */
export function refreshRealtime() {
  return post<RealtimeAll>('/realtime/refresh')
}
