import type { LineChartProps } from '@/types/chart'
import { formatDate, formatNumber } from './formatters'
import { getChartColors, sampleData } from './utils'
import {
  CartesianGrid,
  Line,
  LineChart as ReLineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export const LineChart = ({ data, title, yAxisLabel, color, height = 260 }: LineChartProps) => {
  const colors = getChartColors()
  const chartData = sampleData(data)
  const strokeColor = color || colors.line

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
          <ReLineChart data={chartData} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatDate}
              tick={{ fill: colors.text }}
              interval="preserveEnd"
            />
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
            <Tooltip
              formatter={(value: number) => formatNumber(Number(value))}
              labelFormatter={formatDate}
              wrapperStyle={{ fontSize: 12 }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={strokeColor}
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </ReLineChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
