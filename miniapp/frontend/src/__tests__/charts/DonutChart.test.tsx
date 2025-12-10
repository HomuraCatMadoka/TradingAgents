import { describe, it, expect, beforeAll, afterAll } from 'vitest'
import { render, screen } from '@testing-library/react'
import { DonutChart } from '@/components/charts/DonutChart'

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

describe('DonutChart', () => {
  let restore: () => void

  beforeAll(() => {
    restore = setupDomMocks()
  })

  afterAll(() => {
    restore()
  })

  it('渲染数据并显示总计', () => {
    const data = [
      { name: 'Ethereum', value: 60 },
      { name: 'BSC', value: 40 },
    ]

    render(
      <div style={{ width: 400, height: 300 }}>
        <DonutChart data={data} title="链分布" height={240} />
      </div>,
    )

    expect(screen.getByText('链分布')).toBeInTheDocument()
    const wrapper = screen.getByTestId('chart-wrapper')
    expect(wrapper).toHaveStyle({ height: '240px' })
    expect(screen.getByText('100.00')).toBeInTheDocument()
  })

  it('无数据时显示空状态', () => {
    render(<DonutChart data={[]} />)
    expect(screen.getByText('暂无数据')).toBeInTheDocument()
  })
})
