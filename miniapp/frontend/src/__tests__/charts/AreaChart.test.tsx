import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import { AreaChart } from '@/components/charts/AreaChart'

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

describe('AreaChart', () => {
  let restore: () => void

  beforeAll(() => {
    restore = setupDomMocks()
  })

  afterAll(() => {
    restore()
  })

  it('渲染多协议面积图并应用默认配色与高度', () => {
    const data = [
      { timestamp: '2025-01-01', aave: 120, uniswap: 80 },
      { timestamp: '2025-01-02', aave: 150, uniswap: 90 },
    ]

    render(
      <div style={{ width: 400, height: 320 }}>
        <AreaChart data={data} protocols={['aave', 'uniswap']} title="TVL 对比" height={280} />
      </div>,
    )

    expect(screen.getByText('TVL 对比')).toBeInTheDocument()
    const wrapper = screen.getByTestId('chart-wrapper')
    expect(wrapper).toHaveStyle({ height: '280px' })
    expect(wrapper.querySelector('path[fill="#3b82f6"]')).not.toBeNull()
    expect(wrapper.querySelector('path[fill="#10b981"]')).not.toBeNull()
  })

  it('无数据或协议时展示空状态', () => {
    render(<AreaChart data={[]} protocols={[]} />)
    expect(screen.getByText('暂无数据')).toBeInTheDocument()
  })
})
