import { apiClient } from './api'

export type WatchlistItem = {
  id: number
  protocolName: string
  conditionType: string
  threshold: number
  isActive: boolean
  alertMessage?: string | null
  lastNotified?: string | null
  createdAt: string
  updatedAt: string
}

type RawWatchlist = {
  id: number
  protocol_name: string
  condition_type: string
  threshold: number
  is_active: boolean
  alert_message?: string | null
  last_notified?: string | null
  created_at: string
  updated_at: string
}

const mapWatchlist = (item: RawWatchlist): WatchlistItem => ({
  id: item.id,
  protocolName: item.protocol_name,
  conditionType: item.condition_type,
  threshold: item.threshold,
  isActive: item.is_active,
  alertMessage: item.alert_message ?? null,
  lastNotified: item.last_notified ?? null,
  createdAt: item.created_at,
  updatedAt: item.updated_at,
})

export const getWatchlist = async (
  active?: boolean,
): Promise<WatchlistItem[]> => {
  const response = await apiClient.get<{ data: RawWatchlist[] }>(
    '/api/watchlist',
    { params: active !== undefined ? { active } : undefined },
  )
  return (response.data.data ?? []).map(mapWatchlist)
}

export const createWatchlist = async (payload: {
  protocolName: string
  conditionType: string
  threshold: number
  isActive?: boolean
  alertMessage?: string
}): Promise<WatchlistItem> => {
  const response = await apiClient.post<{ data: RawWatchlist }>('/api/watchlist', {
    protocol_name: payload.protocolName,
    condition_type: payload.conditionType,
    threshold: payload.threshold,
    is_active: payload.isActive ?? true,
    alert_message: payload.alertMessage,
  })
  return mapWatchlist(response.data.data)
}

export const updateWatchlist = async (
  id: number,
  payload: {
    conditionType?: string
    threshold?: number
    isActive?: boolean
    alertMessage?: string | null
  },
): Promise<WatchlistItem> => {
  const response = await apiClient.patch<{ data: RawWatchlist }>(
    `/api/watchlist/${id}`,
    {
      condition_type: payload.conditionType,
      threshold: payload.threshold,
      is_active: payload.isActive,
      alert_message: payload.alertMessage,
    },
  )
  return mapWatchlist(response.data.data)
}

export const batchUpdateWatchlist = async (ids: number[], isActive: boolean) => {
  await apiClient.patch('/api/watchlist/batch', { ids, is_active: isActive })
  return true
}

export const deleteWatchlist = async (id: number) => {
  await apiClient.delete(`/api/watchlist/${id}`)
  return true
}
