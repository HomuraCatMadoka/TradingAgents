import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/services/api'
import { getDetail, getHistory, getList, getMarketData, getPools, triggerAnalysis } from '@/services/protocols'

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

const mockedApi = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
}

beforeEach(() => {
  mockedApi.get.mockReset()
  mockedApi.post.mockReset()
})

describe('protocols service', () => {
  it('列表接口返回协议数组', async () => {
    mockedApi.get.mockResolvedValue({
      data: { data: { protocols: [{ id: '1', name: 'A' }], count: 1 } },
    })
    const list = await getList({ search: 'a' })
    expect(mockedApi.get).toHaveBeenCalledWith('/api/protocols', {
      params: { search: 'a' },
    })
    expect(list[0].name).toBe('A')
  })

  it('详情与市场/池子数据', async () => {
    mockedApi.get.mockResolvedValueOnce({ data: { data: { id: 'a', name: 'A' } } })
    const detail = await getDetail('a')
    expect(detail?.name).toBe('A')

    mockedApi.get.mockResolvedValueOnce({ data: { data: [{ id: 'pool' }] } })
    await getPools('a', { limit: 2 })
    expect(mockedApi.get).toHaveBeenCalledWith('/api/protocols/a/pools', {
      params: { limit: 2 },
    })

    mockedApi.get.mockResolvedValueOnce({ data: { data: { price: 1 } } })
    await getMarketData('a')
    expect(mockedApi.get).toHaveBeenCalledWith('/api/protocols/a/market-data')
  })

  it('历史与触发分析', async () => {
    mockedApi.get.mockResolvedValueOnce({ data: { data: [{ timestamp: 1, value: 1 }] } })
    await getHistory('a', '30d')
    expect(mockedApi.get).toHaveBeenCalledWith('/api/protocols/a/history', {
      params: { period: '30d' },
    })

    mockedApi.post.mockResolvedValue({
      data: { data: { record_id: 1, protocol: 'a', status: 'queued' } },
    })
    const result = await triggerAnalysis('a')
    expect(mockedApi.post).toHaveBeenCalledWith('/api/protocols/a/analyze')
    expect(result.record_id).toBe(1)
  })
})
