import { useId } from 'react'
import type { BarChartProps } from '@/types/chart'
import { formatNumber } from './formatters'
import { getChartColors, sampleData } from './utils'
import {
  Bar,
  BarChart as ReBarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export const BarChart = ({ data, title, yAxisLabel, color, height = 260 }: BarChartProps) => {
  const colors = getChartColors()
  const chartData = sampleData(data)
  const fillColor = color || colors.line
  const gradientId = useId()

  if (!chartData || chartData.length === 0) {
    return <div className="text-sm text-gray-500">暂无数据</div>
  }

  return (
    <div className="w-full">
      {title ? (
        <div className="mb-2 text-base font-medium" data-testid="chart-title">
          {title}
        </div>
      ) : null}
      <div style={{ width: '100%', height }} data-testid="chart-wrapper">
        <ResponsiveContainer>
          <ReBarChart data={chartData} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
            <defs>
              <linearGradient id={gradientId} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={fillColor} stopOpacity={0.9} />
                <stop offset="100%" stopColor={fillColor} stopOpacity={0.4} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            <XAxis dataKey="name" tick={{ fill: colors.text }} interval="preserveEnd" />
            <YAxis
              tickFormatter={formatNumber}
              tick={{ fill: colors.text }}
              width={50}
              label={
                yAxisLabel
                  ? { value: yAxisLabel, angle: -90, position: 'insideLeft', fill: colors.text }
                  : undefined
              }
            />
            <Tooltip formatter={(value: number) => formatNumber(Number(value))} />
            <Bar dataKey="value" radius={[6, 6, 0, 0]} fill={`url(#${gradientId})`} />
          </ReBarChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
