import type { AuthResponse, AuthResult, AuthTokens } from '@/types/auth'

export const REFRESH_TOKEN_KEY = 'refresh_token'

let accessTokenMemory: string | null = null

export const getAccessToken = () => accessTokenMemory

export const setAccessToken = (token: string | null) => {
  accessTokenMemory = token ?? null
}

const readStorage = () => {
  try {
    return window.localStorage
  } catch {
    return null
  }
}

export const getRefreshToken = () => readStorage()?.getItem(REFRESH_TOKEN_KEY) ?? null

export const setRefreshToken = (token: string | null) => {
  const storage = readStorage()
  if (!storage) return
  if (token) {
    storage.setItem(REFRESH_TOKEN_KEY, token)
  } else {
    storage.removeItem(REFRESH_TOKEN_KEY)
  }
}

export const clearRefreshToken = () => setRefreshToken(null)

export const clearTokens = () => {
  setAccessToken(null)
  clearRefreshToken()
}

const base64Decode = (value: string) => {
  try {
    if (typeof atob === 'function') {
      return atob(value)
    }
    // @ts-expect-error Buffer 在浏览器构建中不存在，但测试环境需要兜底
    return Buffer.from(value, 'base64').toString('utf-8')
  } catch {
    return ''
  }
}

export const parseJwtPayload = (token: string): Record<string, unknown> => {
  const parts = token.split('.')
  if (parts.length < 2) return {}
  const decoded = base64Decode(parts[1])
  try {
    return JSON.parse(decoded)
  } catch {
    return {}
  }
}

export const getTokenExpiration = (token: string): number | null => {
  const payload = parseJwtPayload(token) as { exp?: number }
  if (!payload?.exp) return null
  return payload.exp * 1000
}

export const isTokenExpired = (token: string): boolean => {
  const exp = getTokenExpiration(token)
  if (!exp) return false
  return Date.now() >= exp
}

export const extractAuthResult = (
  data: AuthResponse,
  fallbackRefreshToken: string | null = null,
): AuthResult => {
  const tokens: AuthTokens = {
    accessToken: data.tokens?.accessToken ?? data.accessToken ?? data.token ?? '',
    refreshToken: data.tokens?.refreshToken ?? data.refreshToken ?? fallbackRefreshToken ?? '',
  }

  if (!tokens.accessToken || !tokens.refreshToken) {
    throw new Error('认证响应缺少 token')
  }

  return { user: data.user, tokens, session: data.session ?? null }
}
