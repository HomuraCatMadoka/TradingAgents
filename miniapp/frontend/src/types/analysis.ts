export interface Pagination {
  total: number
  limit: number
  offset: number
  hasMore: boolean
}

export interface PaginatedResult<T> {
  data: T[]
  pagination: Pagination
}

export interface Analysis {
  id: number
  protocolName: string
  queryText?: string
  queryType?: string
  result: Record<string, unknown>
  duration?: number
  cached?: boolean
  createdAt: string
}

export interface AnalysisDetail extends Analysis {
  decision?: string
}

export interface AnalysisListParams {
  page?: number
  limit?: number
  protocol?: string
  queryType?: string
  startDate?: string
  endDate?: string
  search?: string
  sort?: string
}
