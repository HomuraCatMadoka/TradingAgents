import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Dashboard from '@/pages/Dashboard'
import { renderWithClient, flushPromises } from '../test-utils'
import { getList } from '@/services/protocols'
import { listAnalysisHistory } from '@/services/analysis-history'
import { getFavorites } from '@/services/favorites'
import { getWatchlist } from '@/services/watchlist'

vi.mock('@/services/protocols', () => ({ getList: vi.fn() }))
vi.mock('@/services/analysis-history', () => ({ listAnalysisHistory: vi.fn() }))
vi.mock('@/services/favorites', () => ({ getFavorites: vi.fn() }))
vi.mock('@/services/watchlist', () => ({ getWatchlist: vi.fn() }))

const mockedGetList = getList as unknown as ReturnType<typeof vi.fn>
const mockedListHistory = listAnalysisHistory as unknown as ReturnType<typeof vi.fn>
const mockedGetFavorites = getFavorites as unknown as ReturnType<typeof vi.fn>
const mockedGetWatchlist = getWatchlist as unknown as ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Dashboard 页面', () => {
  it('渲染概览与列表', async () => {
    mockedGetList.mockResolvedValue([
      { id: '1', name: 'Aave', tvl: 1000, apy: 5, chain: 'eth' },
      { id: '2', name: 'Uni', tvl: 800, apy: 3 },
    ])
    mockedListHistory.mockResolvedValue({
      data: [
        {
          id: 1,
          protocolName: 'Aave',
          queryType: 'analysis',
          result: {},
          createdAt: 'today',
        },
      ],
      pagination: { total: 1, limit: 5, offset: 0, hasMore: false },
    })
    mockedGetFavorites.mockResolvedValue([
      { id: 1, protocolName: 'Aave', protocolType: 'eth', addedAt: 'now' },
    ])
    mockedGetWatchlist.mockResolvedValue([
      {
        id: 1,
        protocolName: 'Aave',
        conditionType: 'tvl_drop',
        threshold: 10,
        isActive: true,
        createdAt: 'now',
        updatedAt: 'now',
      },
    ])

    const { container, root } = await renderWithClient(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </MemoryRouter>,
    )

    await flushPromises()

    expect(container.textContent).toContain('概览')
    expect(container.textContent).toContain('分析次数')
    expect(container.textContent).toContain('Aave')
    expect(container.textContent).toContain('我的收藏')

    root.unmount()
    container.remove()
  })

  it('出错时展示错误块', async () => {
    mockedGetList.mockRejectedValue(new Error('fail'))
    mockedListHistory.mockRejectedValue(new Error('fail'))
    mockedGetFavorites.mockRejectedValue(new Error('fail'))
    mockedGetWatchlist.mockRejectedValue(new Error('fail'))

    const { container, root } = await renderWithClient(
      <MemoryRouter initialEntries={['/dashboard']}>
        <Routes>
          <Route path="/dashboard" element={<Dashboard />} />
        </Routes>
      </MemoryRouter>,
    )

    await flushPromises()

    expect(container.textContent).toContain('加载失败')

    root.unmount()
    container.remove()
  })
})
