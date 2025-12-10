import { describe, it, expect, beforeEach, vi } from 'vitest'

const renderMock = vi.fn()
const createRootMock = vi.fn(() => ({ render: renderMock }))

vi.mock('react-dom/client', () => ({
  createRoot: createRootMock,
}))

vi.mock('@/App', () => ({ default: () => <div>AppRoot</div> }))

vi.mock('@/components/ThemeProvider', () => ({
  default: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="theme-provider">{children}</div>
  ),
}))

beforeEach(() => {
  document.body.innerHTML = ''
  vi.clearAllMocks()
})

describe('main.tsx', () => {
  it('初始化根节点并渲染应用', async () => {
    const root = document.createElement('div')
    root.id = 'root'
    document.body.appendChild(root)

    await import('@/main')

    expect(createRootMock).toHaveBeenCalledWith(root)
    expect(renderMock).toHaveBeenCalledTimes(1)
  })
})
