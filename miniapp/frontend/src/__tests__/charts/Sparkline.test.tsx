import { describe, it, expect, afterEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import { Sparkline } from '@/components/charts/Sparkline'

afterEach(() => {
  document.documentElement.style.removeProperty('--tg-theme-link-color')
})

describe('Sparkline', () => {
  it('渲染折线并支持自定义尺寸和颜色', () => {
    const { container } = render(<Sparkline data={[1, 2, 3, 4]} color="#ff8800" width={160} height={40} />)
    const wrapper = container.firstElementChild as HTMLDivElement
    expect(wrapper).toHaveStyle({ width: '160px', height: '40px' })
    const path = wrapper.querySelector('path[stroke="#ff8800"]')
    expect(path).not.toBeNull()
  })

  it('使用主题变量作为默认颜色', () => {
    document.documentElement.style.setProperty('--tg-theme-link-color', '#112233')
    const { container } = render(<Sparkline data={[5, 6, 7]} />)
    const path = container.querySelector('path[stroke="#112233"]')
    expect(path).not.toBeNull()
  })

  it('无数据时显示空提示', () => {
    render(<Sparkline data={[]} />)
    expect(screen.getByText('暂无数据')).toBeInTheDocument()
  })
})
