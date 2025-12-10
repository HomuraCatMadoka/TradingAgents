import { describe, expect, it, beforeEach } from 'vitest'
import {
  clearRefreshToken,
  clearTokens,
  getAccessToken,
  getRefreshToken,
  getTokenExpiration,
  isTokenExpired,
  parseJwtPayload,
  setAccessToken,
  setRefreshToken,
} from '@/utils/auth'

const createJwt = (expSecondsFromNow: number) => {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }))
  const payload = btoa(
    JSON.stringify({ exp: Math.floor(Date.now() / 1000) + expSecondsFromNow }),
  )
  return `${header}.${payload}.signature`
}

beforeEach(() => {
  clearTokens()
  localStorage.clear()
})

describe('auth utils', () => {
  it('管理内存与本地 refresh token', () => {
    setAccessToken('access-1')
    setRefreshToken('refresh-1')

    expect(getAccessToken()).toBe('access-1')
    expect(getRefreshToken()).toBe('refresh-1')

    clearRefreshToken()
    expect(getRefreshToken()).toBeNull()
  })

  it('解析 JWT 过期时间', () => {
    const token = createJwt(60)
    const payload = parseJwtPayload(token)
    expect(payload.exp).toBeTypeOf('number')
    expect(isTokenExpired(token)).toBe(false)

    const expired = createJwt(-60)
    expect(isTokenExpired(expired)).toBe(true)
    expect(getTokenExpiration(expired)).toBeLessThan(Date.now())
  })
})
