import { apiClient } from './api'

export type Favorite = {
  id: number
  protocolName: string
  protocolType?: string | null
  addedAt: string
}

type RawFavorite = {
  id: number
  protocol_name: string
  protocol_type?: string | null
  added_at: string
}

const mapFavorite = (item: RawFavorite): Favorite => ({
  id: item.id,
  protocolName: item.protocol_name,
  protocolType: item.protocol_type ?? null,
  addedAt: item.added_at,
})

export const getFavorites = async (chain?: string): Promise<Favorite[]> => {
  const response = await apiClient.get<{ data: RawFavorite[] }>('/api/favorites', {
    params: chain ? { chain } : undefined,
  })
  return (response.data.data ?? []).map(mapFavorite)
}

export const addFavorite = async (payload: {
  protocolName: string
  protocolType?: string
}): Promise<Favorite> => {
  const response = await apiClient.post<{ data: RawFavorite }>('/api/favorites', {
    protocol_name: payload.protocolName,
    protocol_type: payload.protocolType,
  })
  return mapFavorite(response.data.data)
}

export const deleteFavorite = async (id: number) => {
  await apiClient.delete(`/api/favorites/${id}`)
  return true
}

export const deleteFavoritesBatch = async (ids: number[]) => {
  await apiClient.delete('/api/favorites/batch', { data: { ids } })
  return true
}
