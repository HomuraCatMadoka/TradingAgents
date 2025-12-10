import type { AuthResponse, AuthResult } from '@/types/auth'
import { apiClient } from './api'
import { useAuthStore } from '@/store/auth'
import {
  extractAuthResult,
  getAccessToken as getCachedAccessToken,
  getRefreshToken,
  isTokenExpired,
} from '@/utils/auth'

const commitAuth = (result: AuthResult) => {
  useAuthStore.getState().setAuth(result)
  return result
}

export const login = async (initData: string) => {
  const response = await apiClient.post<AuthResponse>(
    '/api/auth/telegram',
    { initData },
    { _skipAuthRefresh: true },
  )
  return commitAuth(extractAuthResult(response.data))
}

export const refresh = async () => {
  const refreshToken = getRefreshToken()
  if (!refreshToken) {
    throw new Error('缺少 refresh token')
  }
  const response = await apiClient.post<AuthResponse>(
    '/api/auth/refresh',
    { refreshToken },
    { _skipAuthRefresh: true },
  )
  return commitAuth(extractAuthResult(response.data, refreshToken))
}

export const logout = async () => {
  try {
    await apiClient.post('/api/auth/logout', undefined, { _skipAuthRefresh: true })
  } catch {
    // 后端登出失败不影响前端清理
  } finally {
    useAuthStore.getState().logout()
  }
}

export const getAccessToken = () => useAuthStore.getState().accessToken ?? getCachedAccessToken()

export const isAuthenticated = () => {
  const state = useAuthStore.getState()
  if (state.accessToken && !isTokenExpired(state.accessToken)) return true

  const refreshToken = state.refreshToken ?? getRefreshToken()
  if (refreshToken && !isTokenExpired(refreshToken)) return true
  return false
}

export const telegramAuth = login
