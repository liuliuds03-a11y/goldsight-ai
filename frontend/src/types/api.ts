/** 后端统一响应格式 */
export interface ApiResponse<T = unknown> {
  code: number
  message?: string
  data: T
}

/** 健康检查数据 */
export interface HealthData {
  status: string
  service: string
}

/** 通用分页参数 */
export interface PaginationParams {
  page?: number
  pageSize?: number
}

/** 通用分页响应 */
export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  pageSize: number
}
