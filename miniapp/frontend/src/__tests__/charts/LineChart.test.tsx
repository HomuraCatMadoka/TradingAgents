import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import { LineChart } from '@/components/charts/LineChart'

const setupDomMocks = () => {
  const original = HTMLElement.prototype.getBoundingClientRect
  // @ts-expect-error jsdom 环境需要模拟尺寸
  HTMLElement.prototype.getBoundingClientRect = () => ({
    width: 400,
    height: 300,
    top: 0,
    left: 0,
    right: 400,
    bottom: 300,
    x: 0,
    y: 0,
    toJSON: () => {},
  })

  Object.defineProperty(HTMLElement.prototype, 'clientWidth', {
    configurable: true,
    get: () => 400,
  })
  Object.defineProperty(HTMLElement.prototype, 'clientHeight', {
    configurable: true,
    get: () => 300,
  })

  // @ts-expect-error 覆盖全局 ResizeObserver
  global.ResizeObserver = class {
    observe() {}
    unobserve() {}
    disconnect() {}
  }

  return () => {
    HTMLElement.prototype.getBoundingClientRect = original
    Reflect.deleteProperty(HTMLElement.prototype, 'clientWidth')
    Reflect.deleteProperty(HTMLElement.prototype, 'clientHeight')
    // @ts-expect-error 清理模拟
    delete global.ResizeObserver
  }
}

describe('LineChart', () => {
  let restore: () => void

  beforeAll(() => {
    restore = setupDomMocks()
  })

  afterAll(() => {
    restore()
  })

  it('渲染数据并展示标题', () => {
    const data = [
      { timestamp: '2025-01-01', value: 100 },
      { timestamp: '2025-01-02', value: 200 },
    ]

    render(
      <div style={{ width: 400, height: 300 }}>
        <LineChart data={data} title="TVL 趋势" color="#ef4444" yAxisLabel="TVL" height={200} />
      </div>,
    )

    expect(screen.getByText('TVL 趋势')).toBeInTheDocument()
    const wrapper = screen.getByTestId('chart-wrapper')
    expect(wrapper).toHaveStyle({ height: '200px' })
    const line = wrapper.querySelector('path[stroke="#ef4444"]')
    expect(line).not.toBeNull()
  })

  it('无数据时显示空状态', () => {
    render(<LineChart data={[]} />)
    expect(screen.getByText('暂无数据')).toBeInTheDocument()
  })
})
