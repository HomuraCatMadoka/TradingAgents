import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest'
import { render, screen, waitFor, cleanup } from '@testing-library/react'
import App from '@/App'
import WebApp from '@twa-dev/sdk'
import { useAuthStore } from '@/store/auth'
import { login, refresh } from '@/services/auth'
import { getRefreshToken, isTokenExpired } from '@/utils/auth'

vi.mock('@twa-dev/sdk', () => {
  const mock = {
    ready: vi.fn(),
    expand: vi.fn(),
    initData: 'mock-init-data',
    onEvent: vi.fn(),
    offEvent: vi.fn(),
    colorScheme: 'light',
    themeParams: {},
  }
  return { default: mock }
})

vi.mock('@/router', () => ({
  default: () => <div data-testid="app-router">APP ROUTER</div>,
}))

vi.mock('@/hooks/useTelegramTheme', () => ({
  useTelegramTheme: vi.fn(() => 'light'),
}))

vi.mock('@/services/auth', () => ({
  login: vi.fn(),
  refresh: vi.fn(),
}))

vi.mock('@/utils/auth', async () => {
  const actual = await vi.importActual<typeof import('@/utils/auth')>('@/utils/auth')
  return {
    ...actual,
    getRefreshToken: vi.fn(),
    isTokenExpired: vi.fn(),
  }
})

type MockFn = ReturnType<typeof vi.fn>

const webAppMock = WebApp as unknown as {
  ready: MockFn
  expand: MockFn
  initData: string
  onEvent: MockFn
  offEvent: MockFn
}

const mockLogin = login as unknown as MockFn
const mockRefresh = refresh as unknown as MockFn
const mockGetRefreshToken = getRefreshToken as unknown as MockFn
const mockIsTokenExpired = isTokenExpired as unknown as MockFn

const resetAuthStore = () => {
  useAuthStore.setState((state) => ({
    ...state,
    user: null,
    accessToken: null,
    refreshToken: null,
    session: null,
  }))
  localStorage.clear()
}

beforeEach(() => {
  vi.clearAllMocks()
  resetAuthStore()
  webAppMock.initData = 'mock-init-data'
  mockIsTokenExpired.mockImplementation((token?: string) => token?.includes('expired'))
  mockGetRefreshToken.mockReturnValue(null)
})

afterEach(() => {
  cleanup()
  resetAuthStore()
})

describe('App', () => {
  it('初始化 Telegram 并在 token 有效时直接渲染路由', async () => {
    useAuthStore.setState((state) => ({
      ...state,
      accessToken: 'valid-token',
      refreshToken: 'refresh-token',
    }))

    render(<App />)

    await waitFor(() => expect(screen.getByTestId('app-router')).toBeInTheDocument())

    expect(webAppMock.ready).toHaveBeenCalled()
    expect(webAppMock.expand).toHaveBeenCalled()
    expect(mockLogin).not.toHaveBeenCalled()
    expect(mockRefresh).not.toHaveBeenCalled()
  })

  it('initData 缺失时展示错误并登出', async () => {
    webAppMock.initData = ''
    const logoutSpy = vi.spyOn(useAuthStore.getState(), 'logout')

    render(<App />)

    await waitFor(() => expect(screen.getByText('认证失败')).toBeInTheDocument())
    expect(logoutSpy).toHaveBeenCalled()
    expect(mockLogin).not.toHaveBeenCalled()

    logoutSpy.mockRestore()
  })

  it('refresh token 可用时优先刷新', async () => {
    mockIsTokenExpired.mockImplementation((token?: string) => token === 'expired')
    useAuthStore.setState((state) => ({
      ...state,
      accessToken: 'expired',
      refreshToken: 'fresh-token',
    }))
    mockRefresh.mockResolvedValue(undefined)

    render(<App />)

    await waitFor(() => expect(mockRefresh).toHaveBeenCalledTimes(1))
    expect(screen.getByTestId('app-router')).toBeInTheDocument()
  })

  it('缺少 refresh token 时使用 initData 登录', async () => {
    mockGetRefreshToken.mockReturnValue(null)
    mockLogin.mockResolvedValue(undefined)
    webAppMock.initData = 'init-data'

    render(<App />)

    await waitFor(() => expect(mockLogin).toHaveBeenCalledWith('init-data'))
    expect(screen.getByTestId('app-router')).toBeInTheDocument()
  })

  it('登录失败时提示错误并清空凭证', async () => {
    mockLogin.mockRejectedValue(new Error('login failed'))
    webAppMock.initData = 'init-data'
    const logoutSpy = vi.spyOn(useAuthStore.getState(), 'logout')

    render(<App />)

    await waitFor(() => expect(screen.getByText('认证失败')).toBeInTheDocument())
    expect(logoutSpy).toHaveBeenCalled()

    logoutSpy.mockRestore()
  })
})
