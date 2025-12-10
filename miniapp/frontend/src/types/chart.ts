export interface LineChartDatum {
  timestamp: string
  value: number
  label?: string
}

export interface LineChartProps {
  data: LineChartDatum[]
  title?: string
  yAxisLabel?: string
  color?: string
  height?: number
}

export interface BarChartDatum {
  name: string
  value: number
}

export interface BarChartProps {
  data: BarChartDatum[]
  title?: string
  yAxisLabel?: string
  color?: string
  height?: number
}

export interface AreaChartDatum {
  timestamp: string
  [protocol: string]: string | number
}

export interface AreaChartProps {
  data: AreaChartDatum[]
  protocols: string[]
  title?: string
  height?: number
}

export interface DonutChartDatum {
  name: string
  value: number
}

export interface DonutChartProps {
  data: DonutChartDatum[]
  title?: string
  height?: number
}

export interface SparklineProps {
  data: number[]
  color?: string
  width?: number
  height?: number
}
