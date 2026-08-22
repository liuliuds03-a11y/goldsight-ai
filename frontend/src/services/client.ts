import axios, { type AxiosInstance, type AxiosResponse, type InternalAxiosRequestConfig } from 'axios'
import type { ApiResponse } from '@/types'

/** 创建 Axios 实例 */
const client: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

/** 请求拦截器 */
client.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // 可在此处添加 token 等认证信息
    return config
  },
  (error) => {
    return Promise.reject(error)
  },
)

/** 响应拦截器 — 统一处理错误 */
client.interceptors.response.use(
  (response: AxiosResponse<ApiResponse>) => {
    const { data } = response

    // 后端返回的业务状态码非 200 时，视为业务错误
    if (data.code !== undefined && data.code !== 200) {
      const message = data.message || `请求失败 (${data.code})`
      console.error('[API 业务错误]', message)
      return Promise.reject(new Error(message))
    }

    return response
  },
  (error) => {
    if (axios.isCancel(error)) {
      console.log('[请求已取消]', error.message)
      return Promise.reject(error)
    }

    if (error.response) {
      const { status, data } = error.response
      const message = data?.message || `服务器错误 (${status})`

      switch (status) {
        case 401:
          console.error('[认证失败] 请重新登录')
          break
        case 403:
          console.error('[权限不足] 禁止访问')
          break
        case 404:
          console.error('[资源不存在]', error.config?.url)
          break
        case 500:
          console.error('[服务器内部错误]')
          break
        default:
          console.error(`[HTTP ${status}]`, message)
      }
    } else if (error.code === 'ECONNABORTED') {
      console.error('[请求超时] 请稍后重试')
    } else {
      console.error('[网络错误] 请检查网络连接')
    }

    return Promise.reject(error)
  },
)

/** 封装 GET 请求 */
export async function get<T>(url: string, params?: Record<string, unknown>): Promise<ApiResponse<T>> {
  const response = await client.get<ApiResponse<T>>(url, { params })
  return response.data
}

/** 封装 POST 请求 */
export async function post<T>(url: string, data?: unknown): Promise<ApiResponse<T>> {
  const response = await client.post<ApiResponse<T>>(url, data)
  return response.data
}

/** 封装 PUT 请求 */
export async function put<T>(url: string, data?: unknown): Promise<ApiResponse<T>> {
  const response = await client.put<ApiResponse<T>>(url, data)
  return response.data
}

/** 封装 DELETE 请求 */
export async function del<T>(url: string): Promise<ApiResponse<T>> {
  const response = await client.delete<ApiResponse<T>>(url)
  return response.data
}

export default client
