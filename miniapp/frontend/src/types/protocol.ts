export interface ProtocolMetric {
  label: string
  value: string | number
  trend?: number
}

export interface ProtocolPool {
  id: string
  name: string
  chain?: string
  tvl?: number
  apy?: number
  volume24h?: number
}

export interface MarketData {
  price?: number
  change24h?: number
  volume24h?: number
  marketCap?: number
}

export interface Protocol {
  id: string
  name: string
  slug?: string
  chain?: string
  category?: string
  tvl?: number
  apy?: number
  isFavorite?: boolean
  tags?: string[]
  metrics?: ProtocolMetric[]
}

export interface ProtocolDetail extends Protocol {
  description?: string
  riskScore?: number
  tvlHistory?: Array<{ timestamp: number; value: number }>
  apyHistory?: Array<{ timestamp: number; value: number }>
  marketData?: MarketData
  pools?: ProtocolPool[]
}
