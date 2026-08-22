import { get } from './client'
import type { HealthData } from '@/types'

/** 健康检查 */
export function fetchHealth() {
  return get<HealthData>('/health')
}
