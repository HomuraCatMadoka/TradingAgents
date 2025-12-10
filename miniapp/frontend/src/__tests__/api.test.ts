import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { apiClient } from '@/services/api'
import { useAuthStore } from '@/store/auth'
import { clearTokens } from '@/utils/auth'

const originalAdapter = apiClient.defaults.adapter

const createResponse = (config: any, data: any, status = 200) =>
  Promise.resolve({
    config,
    data,
    status,
    statusText: status === 200 ? 'OK' : 'Error',
    headers: {},
    request: {},
  })

beforeEach(() => {
  useAuthStore.getState().logout()
  clearTokens()
  localStorage.clear()
})

afterEach(() => {
  apiClient.defaults.adapter = originalAdapter
  useAuthStore.getState().logout()
  clearTokens()
  localStorage.clear()
})

describe('api 拦截器', () => {
  it('401 时自动刷新并重试原始请求', async () => {
    let protectedCalls = 0
    let refreshCalls = 0

    apiClient.defaults.adapter = (config) => {
      if (config.url === '/api/auth/refresh') {
        refreshCalls += 1
        return createResponse(config, {
          user: { id: 'u1' },
          tokens: { accessToken: 'access-new', refreshToken: 'refresh-new' },
        })
      }
      if (config.url === '/api/protected') {
        protectedCalls += 1
        if (protectedCalls === 1) {
          return createResponse(config, {}, 401)
        }
        return createResponse(config, { ok: true, auth: config.headers?.Authorization })
      }
      return createResponse(config, {}, 404)
    }

    useAuthStore.getState().setAuth({
      user: { id: 'u1' },
      tokens: { accessToken: 'expired', refreshToken: 'refresh-old' },
      session: null,
    })

    const response = await apiClient.get('/api/protected')

    expect(response.data).toEqual({ ok: true, auth: 'Bearer access-new' })
    expect(protectedCalls).toBe(2)
    expect(refreshCalls).toBe(1)
  })

  it('刷新失败会清空凭证并拒绝原请求', async () => {
    let refreshCalls = 0

    apiClient.defaults.adapter = (config) => {
      if (config.url === '/api/auth/refresh') {
        refreshCalls += 1
        return createResponse(config, {}, 401)
      }
      if (config.url === '/api/protected') {
        return createResponse(config, {}, 401)
      }
      return createResponse(config, {}, 404)
    }

    useAuthStore.getState().setAuth({
      user: { id: 'u1' },
      tokens: { accessToken: 'expired', refreshToken: 'refresh-old' },
      session: null,
    })

    await expect(apiClient.get('/api/protected')).rejects.toBeTruthy()

    expect(refreshCalls).toBe(1)
    expect(useAuthStore.getState().accessToken).toBeNull()
    expect(useAuthStore.getState().refreshToken).toBeNull()
  })

  it('并发 401 请求共享刷新结果', async () => {
    let protectedCalls = 0
    let refreshCalls = 0

    apiClient.defaults.adapter = (config) => {
      if (config.url === '/api/auth/refresh') {
        refreshCalls += 1
        return createResponse(config, {
          user: { id: 'u1' },
          tokens: { accessToken: 'access-shared', refreshToken: 'refresh-shared' },
        })
      }
      if (config.url === '/api/protected') {
        protectedCalls += 1
        if (protectedCalls <= 2) {
          return createResponse(config, {}, 401)
        }
        return createResponse(config, { ok: true, call: protectedCalls, auth: config.headers?.Authorization })
      }
      return createResponse(config, {}, 404)
    }

    useAuthStore.getState().setAuth({
      user: { id: 'u1' },
      tokens: { accessToken: 'expired', refreshToken: 'refresh-old' },
      session: null,
    })

    const [resp1, resp2] = await Promise.all([
      apiClient.get('/api/protected'),
      apiClient.get('/api/protected'),
    ])

    expect(refreshCalls).toBe(1)
    expect(protectedCalls).toBe(4)
    expect(resp1.data.auth).toBe('Bearer access-shared')
    expect(resp2.data.auth).toBe('Bearer access-shared')
  })
})
