import type { SparklineProps } from '@/types/chart'
import { getChartColors, sampleData } from './utils'
import { Line, LineChart as ReLineChart } from 'recharts'

export const Sparkline = ({ data, color, width = 100, height = 30 }: SparklineProps) => {
  const colors = getChartColors()
  const chartData = sampleData(data).map((value, index) => ({ index, value }))
  const strokeColor = color || colors.line

  if (!chartData || chartData.length === 0) {
    return <div className="text-xs text-gray-500">暂无数据</div>
  }

  return (
    <div style={{ width, height }}>
      <ReLineChart
        width={width}
        height={height}
        data={chartData}
        margin={{ top: 2, right: 2, bottom: 2, left: 2 }}
      >
        <Line
          type="monotone"
          dataKey="value"
          stroke={strokeColor}
          strokeWidth={1.5}
          dot={false}
          isAnimationActive={false}
        />
      </ReLineChart>
    </div>
  )
}
