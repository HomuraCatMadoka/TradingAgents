import type { AreaChartProps } from '@/types/chart'
import { formatDate, formatNumber } from './formatters'
import { defaultPalette, getChartColors, sampleData } from './utils'
import {
  Area,
  AreaChart as ReAreaChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

export const AreaChart = ({ data, protocols, title, height = 260 }: AreaChartProps) => {
  const colors = getChartColors()
  const chartData = sampleData(data)

  if (!chartData || chartData.length === 0 || !protocols || protocols.length === 0) {
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
          <ReAreaChart data={chartData} margin={{ top: 8, right: 8, bottom: 8, left: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            <XAxis
              dataKey="timestamp"
              tickFormatter={formatDate}
              tick={{ fill: colors.text }}
              interval="preserveEnd"
            />
            <YAxis tickFormatter={formatNumber} tick={{ fill: colors.text }} width={50} />
            <Tooltip labelFormatter={formatDate} formatter={(value: number) => formatNumber(Number(value))} />
            {protocols.map((protocol, index) => {
              const paletteColor = defaultPalette[index % defaultPalette.length]
              return (
                <Area
                  key={protocol}
                  type="monotone"
                  dataKey={protocol}
                  stackId="1"
                  stroke={paletteColor}
                  fill={paletteColor}
                  fillOpacity={0.7}
                  isAnimationActive={false}
                />
              )
            })}
          </ReAreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
