import { describe, expect, it, vi } from 'vitest'
import { act } from 'react-dom/test-utils'
import { createRoot } from 'react-dom/client'
import { useState } from 'react'
import ErrorBoundary from '../components/ErrorBoundary'

const Thrower = ({ shouldThrow }: { shouldThrow: boolean }) => {
  if (shouldThrow) {
    throw new Error('boom')
  }
  return <div data-testid="content">safe</div>
}

const renderWithRoot = () => {
  const container = document.createElement('div')
  document.body.appendChild(container)
  const root = createRoot(container)
  return { container, root }
}

describe('ErrorBoundary', () => {
  it('正常渲染子组件', () => {
    const { container, root } = renderWithRoot()
    act(() => {
      root.render(
        <ErrorBoundary>
          <Thrower shouldThrow={false} />
        </ErrorBoundary>,
      )
    })

    expect(container.querySelector('[data-testid="content"]')).not.toBeNull()
    root.unmount()
    container.remove()
  })

  it('捕获错误并渲染默认 fallback', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { container, root } = renderWithRoot()

    act(() => {
      root.render(
        <ErrorBoundary>
          <Thrower shouldThrow />
        </ErrorBoundary>,
      )
    })

    expect(container.textContent).toContain('页面出错了')

    consoleSpy.mockRestore()
    root.unmount()
    container.remove()
  })

  it('点击重试后可以重新渲染子组件', () => {
    const consoleSpy = vi.spyOn(console, 'error').mockImplementation(() => {})
    const { container, root } = renderWithRoot()

    const TestApp = () => {
      const [shouldThrow, setShouldThrow] = useState(true)
      return (
        <ErrorBoundary onReset={() => setShouldThrow(false)}>
          <Thrower shouldThrow={shouldThrow} />
        </ErrorBoundary>
      )
    }

    act(() => {
      root.render(<TestApp />)
    })

    const retryButton = container.querySelector('button')
    expect(retryButton).not.toBeNull()

    act(() => {
      retryButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(container.querySelector('[data-testid="content"]')).not.toBeNull()

    consoleSpy.mockRestore()
    root.unmount()
    container.remove()
  })
})
