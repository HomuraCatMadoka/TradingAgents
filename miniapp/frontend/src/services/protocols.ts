import type { MarketData, Protocol, ProtocolDetail, ProtocolPool } from '@/types/protocol'
import { apiClient } from './api'

export type ProtocolListParams = {
  search?: string
  chain?: string
  limit?: number
}

export type ProtocolListResponse = {
  protocols: Protocol[]
  count: number
}

export const getProtocols = async (
  params: ProtocolListParams = {},
): Promise<ProtocolListResponse> => {
  const response = await apiClient.get<{
    data?: { protocols?: Protocol[]; count?: number }
  }>('/api/protocols', { params })
  const protocols = response.data?.data?.protocols ?? []
  const count = response.data?.data?.count ?? protocols.length
  return { protocols, count }
}

export const getList = async (params: ProtocolListParams = {}) => {
  const { protocols } = await getProtocols(params)
  return protocols
}

export const getDetail = async (slug: string) => {
  const response = await apiClient.get<{ data: ProtocolDetail }>(
    `/api/protocols/${slug}`,
  )
  return response.data.data
}

export const getHistory = async (slug: string, period = '30d') => {
  const response = await apiClient.get<{ data: ProtocolDetail['tvlHistory'] }>(
    `/api/protocols/${slug}/history`,
    { params: { period } },
  )
  return response.data.data ?? []
}

export const getMarketData = async (slug: string) => {
  const response = await apiClient.get<{ data: MarketData }>(
    `/api/protocols/${slug}/market-data`,
  )
  return response.data.data
}

export const getPools = async (
  slug: string,
  params: { chain?: string; limit?: number } = {},
) => {
  const response = await apiClient.get<{ data: ProtocolPool[] }>(
    `/api/protocols/${slug}/pools`,
    { params },
  )
  return response.data.data ?? []
}

export const triggerAnalysis = async (slug: string) => {
  const response = await apiClient.post<{
    data: { record_id: number; status?: string; protocol: string }
  }>(`/api/protocols/${slug}/analyze`)
  return response.data.data
}
