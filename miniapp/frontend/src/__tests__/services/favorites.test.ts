import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiClient } from '@/services/api'
import { addFavorite, deleteFavorite, getFavorites } from '@/services/favorites'

vi.mock('@/services/api', () => ({
  apiClient: {
    get: vi.fn(),
    post: vi.fn(),
    delete: vi.fn(),
  },
}))

const mockedApi = apiClient as unknown as {
  get: ReturnType<typeof vi.fn>
  post: ReturnType<typeof vi.fn>
  delete: ReturnType<typeof vi.fn>
}

beforeEach(() => {
  mockedApi.get.mockReset()
  mockedApi.post.mockReset()
  mockedApi.delete.mockReset()
})

describe('favorites service', () => {
  it('获取收藏列表并映射字段', async () => {
    mockedApi.get.mockResolvedValue({
      data: {
        data: [{ id: 1, protocol_name: 'aave', protocol_type: 'eth', added_at: 'now' }],
      },
    })
    const list = await getFavorites()
    expect(mockedApi.get).toHaveBeenCalledWith('/api/favorites', { params: undefined })
    expect(list[0]).toEqual({
      id: 1,
      protocolName: 'aave',
      protocolType: 'eth',
      addedAt: 'now',
    })
  })

  it('添加收藏时发送正确 payload', async () => {
    mockedApi.post.mockResolvedValue({
      data: { data: { id: 2, protocol_name: 'uni', protocol_type: null, added_at: 'later' } },
    })
    const result = await addFavorite({ protocolName: 'uni' })
    expect(mockedApi.post).toHaveBeenCalledWith('/api/favorites', {
      protocol_name: 'uni',
      protocol_type: undefined,
    })
    expect(result.protocolName).toBe('uni')
  })

  it('删除收藏', async () => {
    mockedApi.delete.mockResolvedValue({ data: { data: { deleted: true } } })
    await deleteFavorite(5)
    expect(mockedApi.delete).toHaveBeenCalledWith('/api/favorites/5')
  })
})
