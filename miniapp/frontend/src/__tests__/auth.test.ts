import { afterEach, beforeEach, describe, expect, it } from 'vitest'
import { apiClient } from '@/services/api'
import { getAccessToken, isAuthenticated, login, logout, refresh } from '@/services/auth'
import { useAuthStore } from '@/store/auth'
import {
  clearTokens,
  getRefreshToken,
  setRefreshToken,
  setAccessToken,
} from '@/utils/auth'

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

const createJwt = (expiresInSeconds: number) => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payload = btoa(
    JSON.stringify({ exp: Math.floor(Date.now() / 1000) + expiresInSeconds }),
  )
  return `${header}.${payload}.signature`
}

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

describe('auth service', () => {
  it('login 持久化 token 并更新 store', async () => {
    apiClient.defaults.adapter = (config) =>
      createResponse(config, {
        user: { id: 'u1' },
        tokens: { accessToken: 'access-1', refreshToken: 'refresh-1' },
        session: null,
      })

    await login('init-data')

    const state = useAuthStore.getState()
    expect(state.accessToken).toBe('access-1')
    expect(state.refreshToken).toBe('refresh-1')
    expect(getRefreshToken()).toBe('refresh-1')
  })

  it('refresh 使用本地 refresh token 并支持后端未返回 refresh 字段', async () => {
    setRefreshToken('stored-refresh')
    useAuthStore
      .getState()
      .setTokens({ accessToken: 'old-access', refreshToken: 'stored-refresh' })

    apiClient.defaults.adapter = (config) => {
      if (config.url === '/api/auth/refresh') {
        return createResponse(config, {
          user: { id: 'u1' },
          token: 'new-access',
          session: null,
        })
      }
      return createResponse(config, {}, 404)
    }

    await refresh()

    const state = useAuthStore.getState()
    expect(state.accessToken).toBe('new-access')
    expect(state.refreshToken).toBe('stored-refresh')
    expect(getAccessToken()).toBe('new-access')
  })

  it('logout 清理本地 token', async () => {
    useAuthStore.getState().setAuth({
      user: { id: 'u1' },
      tokens: { accessToken: 'access-x', refreshToken: 'refresh-x' },
      session: null,
    })

    apiClient.defaults.adapter = (config) => createResponse(config, {})

    await logout()

    const state = useAuthStore.getState()
    expect(state.accessToken).toBeNull()
    expect(state.refreshToken).toBeNull()
    expect(getRefreshToken()).toBeNull()
  })

  it('isAuthenticated 根据 token 过期状态判断', () => {
    const expired = createJwt(-10)
    const valid = createJwt(60)

    useAuthStore
      .getState()
      .setTokens({ accessToken: expired, refreshToken: valid })

    expect(isAuthenticated()).toBe(true)

    setAccessToken(null)
    useAuthStore
      .getState()
      .setTokens({ accessToken: expired, refreshToken: expired })

    expect(isAuthenticated()).toBe(false)
  })
})
