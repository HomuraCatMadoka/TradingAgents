import type { DonutChartProps } from '@/types/chart'
import { formatNumber } from './formatters'
import { defaultPalette, getChartColors, sampleData } from './utils'
import { Cell, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'

export const DonutChart = ({ data, title, height = 260 }: DonutChartProps) => {
  const colors = getChartColors()
  const chartData = sampleData(data)

  if (!chartData || chartData.length === 0) {
    return <div className="text-sm text-gray-500">暂无数据</div>
  }

  const total = chartData.reduce((sum, item) => sum + item.value, 0)

  if (total === 0) {
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
          <PieChart>
            <Pie
              data={chartData}
              dataKey="value"
              nameKey="name"
              innerRadius="60%"
              outerRadius="80%"
              paddingAngle={2}
              isAnimationActive={false}
              labelLine={false}
            >
              {chartData.map((entry, index) => (
                <Cell key={entry.name} fill={defaultPalette[index % defaultPalette.length]} />
              ))}
            </Pie>
            <Tooltip
              formatter={(value: number, name: string) => {
                const percent = total ? ((Number(value) / total) * 100).toFixed(1) : '0.0'
                return [`${formatNumber(Number(value))} (${percent}%)`, name]
              }}
              wrapperStyle={{ fontSize: 12 }}
            />
            <text x="50%" y="50%" textAnchor="middle" dominantBaseline="middle" fill={colors.text}>
              {formatNumber(total)}
            </text>
          </PieChart>
        </ResponsiveContainer>
      </div>
    </div>
  )
}
