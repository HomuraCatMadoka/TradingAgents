import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Protocols from '@/pages/Protocols'
import { renderWithClient, flushPromises } from '../test-utils'
import { getList } from '@/services/protocols'

vi.mock('@/services/protocols', () => ({ getList: vi.fn() }))
const mockedGetList = getList as unknown as ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Protocols 页面', () => {
  it('展示协议列表并支持排序', async () => {
    mockedGetList.mockResolvedValue([
      { id: '1', name: 'Alpha', tvl: 100, apy: 2 },
      { id: '2', name: 'Beta', tvl: 200, apy: 5 },
    ])

    const { container, root } = await renderWithClient(
      <MemoryRouter initialEntries={['/protocols']}>
        <Routes>
          <Route path="/protocols" element={<Protocols />} />
        </Routes>
      </MemoryRouter>,
    )

    await flushPromises()

    expect(container.textContent).toContain('协议列表')
    expect(container.textContent).toContain('Beta')
    expect(container.textContent).toContain('Alpha')

    root.unmount()
    container.remove()
  })

  it('错误时提示重试', async () => {
    mockedGetList.mockRejectedValue(new Error('fail'))
    const { container, root } = await renderWithClient(
      <MemoryRouter initialEntries={['/protocols']}>
        <Routes>
          <Route path="/protocols" element={<Protocols />} />
        </Routes>
      </MemoryRouter>,
    )

    await flushPromises()
    expect(container.textContent).toContain('加载失败')

    root.unmount()
    container.remove()
  })
})
