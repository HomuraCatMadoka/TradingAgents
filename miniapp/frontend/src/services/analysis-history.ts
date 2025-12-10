import type { Analysis, AnalysisListParams, PaginatedResult } from '@/types/analysis'
import { apiClient } from './api'

type RawAnalysis = {
  id: number
  protocol_name: string
  query_text?: string
  query_type?: string
  result?: Record<string, unknown>
  duration?: number
  cached?: boolean
  created_at: string
}

type RawPagination = {
  total: number
  limit: number
  offset: number
  has_more: boolean
}

type ListResponse = {
  data: RawAnalysis[]
  pagination: RawPagination
}

const toAnalysis = (item: RawAnalysis): Analysis => ({
  id: item.id,
  protocolName: item.protocol_name,
  queryText: item.query_text,
  queryType: item.query_type,
  result: item.result ?? {},
  duration: item.duration,
  cached: item.cached,
  createdAt: item.created_at,
})

const mapPagination = (pagination?: RawPagination) => ({
  total: pagination?.total ?? 0,
  limit: pagination?.limit ?? 0,
  offset: pagination?.offset ?? 0,
  hasMore: Boolean(pagination?.has_more),
})

export const listAnalysisHistory = async (
  params: AnalysisListParams = {},
): Promise<PaginatedResult<Analysis>> => {
  const response = await apiClient.get<{ data: ListResponse }>(
    '/api/analysis-history',
    { params },
  )
  const payload = response.data.data
  return {
    data: (payload?.data ?? []).map(toAnalysis),
    pagination: mapPagination(payload?.pagination),
  }
}

export const getAnalysisDetail = async (id: number): Promise<Analysis> => {
  const response = await apiClient.get<{ data: RawAnalysis }>(
    `/api/analysis-history/${id}`,
  )
  return toAnalysis(response.data.data)
}

export const deleteAnalysisRecord = async (id: number) => {
  await apiClient.delete(`/api/analysis-history/${id}`)
  return true
}
