import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { type ReactNode } from 'react'
import { Outlet } from 'react-router-dom'
import { useAuthStore } from '@/store/auth'
import AppRouter from '@/router'

const pageMock = (name: string) => () => <div>{name}</div>

let initialPath = '/dashboard'

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom')
  const MemoryWrapper = ({ children }: { children: ReactNode }) => (
    <actual.MemoryRouter initialEntries={[initialPath]}>{children}</actual.MemoryRouter>
  )

  return { ...actual, BrowserRouter: MemoryWrapper }
})

vi.mock('@/components/Layout', () => ({
  default: () => (
    <div data-testid="layout">
      <Outlet />
    </div>
  ),
}))

vi.mock('@/pages/Dashboard', () => ({ default: pageMock('DashboardPage') }))
vi.mock('@/pages/Analysis', () => ({ default: pageMock('AnalysisPage') }))
vi.mock('@/pages/Protocols', () => ({ default: pageMock('ProtocolsPage') }))
vi.mock('@/pages/ProtocolDetail', () => ({ default: pageMock('ProtocolDetailPage') }))
vi.mock('@/pages/History', () => ({ default: pageMock('HistoryPage') }))
vi.mock('@/pages/Favorites', () => ({ default: pageMock('FavoritesPage') }))
vi.mock('@/pages/Settings', () => ({ default: pageMock('SettingsPage') }))
vi.mock('@/pages/Watchlist', () => ({ default: pageMock('WatchlistPage') }))

beforeEach(() => {
  initialPath = '/dashboard'
  useAuthStore.getState().logout()
})

describe('AppRouter', () => {
  it('未认证时跳转错误页', () => {
    render(<AppRouter />)
    expect(screen.getByText('未认证')).toBeInTheDocument()
    expect(screen.getByText('缺少有效的登录状态，请重新打开应用')).toBeInTheDocument()
  })

  it('认证后渲染目标页面', () => {
    initialPath = '/analysis'
    useAuthStore.setState((state) => ({ ...state, accessToken: 'token-xyz' }))

    render(<AppRouter />)

    expect(screen.getByText('AnalysisPage')).toBeInTheDocument()
    expect(screen.getByTestId('layout')).toBeInTheDocument()
  })
})
