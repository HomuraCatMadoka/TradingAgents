import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import { BarChart } from '@/components/charts/BarChart'

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

describe('BarChart', () => {
  let restore: () => void

  beforeAll(() => {
    restore = setupDomMocks()
  })

  afterAll(() => {
    restore()
  })

  it('渲染数据并应用自定义颜色与高度', () => {
    const data = [
      { name: 'Aave', value: 12 },
      { name: 'Uniswap', value: 8 },
    ]

    render(
      <div style={{ width: 400, height: 300 }}>
        <BarChart data={data} title="APY 对比" color="#10b981" yAxisLabel="APY" height={220} />
      </div>,
    )

    expect(screen.getByText('APY 对比')).toBeInTheDocument()
    const wrapper = screen.getByTestId('chart-wrapper')
    expect(wrapper).toHaveStyle({ height: '220px' })
    const stop = wrapper.querySelector('stop[stop-color="#10b981"]')
    expect(stop).not.toBeNull()
  })

  it('无数据时显示空状态', () => {
    render(<BarChart data={[]} />)
    expect(screen.getByText('暂无数据')).toBeInTheDocument()
  })
})
