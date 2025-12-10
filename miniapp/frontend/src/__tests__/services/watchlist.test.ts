import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/services/api'
import {
  batchUpdateWatchlist,
  createWatchlist,
  deleteWatchlist,
  getWatchlist,
  updateWatchlist,
} from '@/services/watchlist'

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    patch: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedApi = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  patch: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

beforeEach(() => {
  mockedApi.get.mockReset()
  mockedApi.post.mockReset()
  mockedApi.patch.mockReset()
  mockedApi.delete.mockReset()
})

describe('watchlist service', () => {
  it('获取监控列表', async () => {
    mockedApi.get.mockResolvedValue({
      data: {
        data: [
          {
            id: 1,
            protocol_name: 'aave',
            condition_type: 'tvl_drop',
            threshold: 10,
            is_active: true,
            created_at: 'now',
            updated_at: 'now',
          },
        ],
      },
    })
    const res = await getWatchlist()
    expect(mockedApi.get).toHaveBeenCalledWith('/api/watchlist', { params: undefined })
    expect(res[0].protocolName).toBe('aave')
    expect(res[0].isActive).toBe(true)
  })

  it('创建监控项', async () => {
    mockedApi.post.mockResolvedValue({
      data: {
        data: {
          id: 2,
          protocol_name: 'uni',
          condition_type: 'apy_rise',
          threshold: 5,
          is_active: true,
          created_at: 'now',
          updated_at: 'now',
        },
      },
    })
    const entry = await createWatchlist({
      protocolName: 'uni',
      conditionType: 'apy_rise',
      threshold: 5,
    })
    expect(mockedApi.post).toHaveBeenCalledWith('/api/watchlist', {
      protocol_name: 'uni',
      condition_type: 'apy_rise',
      threshold: 5,
      is_active: true,
      alert_message: undefined,
    })
    expect(entry.threshold).toBe(5)
  })

  it('更新与批量更新', async () => {
    mockedApi.patch.mockResolvedValue({
      data: {
        data: {
          id: 2,
          protocol_name: 'uni',
          condition_type: 'apy_rise',
          threshold: 6,
          is_active: false,
          created_at: 'now',
          updated_at: 'now',
        },
      },
    })
    const updated = await updateWatchlist(2, { threshold: 6, isActive: false })
    expect(updated.threshold).toBe(6)
    expect(mockedApi.patch).toHaveBeenCalledWith('/api/watchlist/2', {
      condition_type: undefined,
      threshold: 6,
      is_active: false,
      alert_message: undefined,
    })

    mockedApi.patch.mockResolvedValue({ data: { data: { updated: 2 } } })
    await batchUpdateWatchlist([1, 2], true)
    expect(mockedApi.patch).toHaveBeenCalledWith('/api/watchlist/batch', {
      ids: [1, 2],
      is_active: true,
    })
  })

  it('删除监控项', async () => {
    mockedApi.delete.mockResolvedValue({ data: { data: { deleted: true } } })
    await deleteWatchlist(3)
    expect(mockedApi.delete).toHaveBeenCalledWith('/api/watchlist/3')
  })
})
