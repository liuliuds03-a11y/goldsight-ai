import { describe, it, expect } from 'vitest'
import client from '../services/client'

describe('apiClient', () => {
  it('默认 baseURL 为 /api/v1', () => {
    expect(client.defaults.baseURL).toBe('/api/v1')
  })

  it('默认 timeout 为 15 秒', () => {
    expect(client.defaults.timeout).toBe(15000)
  })

  it('响应拦截器已配置', () => {
    expect(client.interceptors.response).toBeDefined()
  })
})
