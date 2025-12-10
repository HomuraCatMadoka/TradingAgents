import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/services/api'
import {
  deleteAnalysisRecord,
  getAnalysisDetail,
  listAnalysisHistory,
} from '@/services/analysis-history'

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedApi = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

beforeEach(() => {
  mockedApi.get.mockReset()
  mockedApi.delete.mockReset()
})

describe('analysis-history service', () => {
  it('列表接口转换字段并保留分页', async () => {
    mockedApi.get.mockResolvedValue({
      data: {
        data: {
          data: [
            {
              id: 1,
              protocol_name: 'aave',
              query_text: 'test',
              query_type: 'analysis',
              result: { ok: true },
              cached: true,
              created_at: '2024-01-01',
            },
          ],
          pagination: { total: 10, limit: 5, offset: 0, has_more: true },
        },
      },
    })

    const result = await listAnalysisHistory({ page: 1, limit: 5 })

    expect(mockedApi.get).toHaveBeenCalledWith('/api/analysis-history', {
      params: { page: 1, limit: 5 },
    })
    expect(result.data[0]).toMatchObject({
      id: 1,
      protocolName: 'aave',
      queryText: 'test',
      cached: true,
    })
    expect(result.pagination).toEqual({
      total: 10,
      limit: 5,
      offset: 0,
      hasMore: true,
    })
  })

  it('获取详情时映射字段', async () => {
    mockedApi.get.mockResolvedValue({
      data: {
        data: {
          id: 2,
          protocol_name: 'uni',
          query_type: 'comparison',
          result: {},
          created_at: '2024-02-01',
        },
      },
    })

    const detail = await getAnalysisDetail(2)
    expect(mockedApi.get).toHaveBeenCalledWith('/api/analysis-history/2')
    expect(detail.protocolName).toBe('uni')
    expect(detail.id).toBe(2)
  })

  it('删除记录会调用 delete 接口', async () => {
    mockedApi.delete.mockResolvedValue({ data: { data: { message: 'deleted' } } })
    const res = await deleteAnalysisRecord(3)
    expect(res).toBe(true)
    expect(mockedApi.delete).toHaveBeenCalledWith('/api/analysis-history/3')
  })
})
