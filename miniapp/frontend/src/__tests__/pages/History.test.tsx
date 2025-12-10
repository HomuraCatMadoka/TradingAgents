import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import History from '@/pages/History'
import { renderWithClient, flushPromises } from '../test-utils'
import { listAnalysisHistory, deleteAnalysisRecord } from '@/services/analysis-history'

vi.mock('@/services/analysis-history', () => ({
  listAnalysisHistory: vi.fn(),
  deleteAnalysisRecord: vi.fn(),
}))

const mockedList = listAnalysisHistory as unknown as ReturnType<typeof vi.fn>
const mockedDelete = deleteAnalysisRecord as unknown as ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.clearAllMocks()
})

describe('History 页面', () => {
  it('分页加载与删除', async () => {
    mockedList
      .mockResolvedValueOnce({
        data: [
          { id: 1, protocolName: 'A', queryType: 'analysis', result: {}, createdAt: 't1' },
        ],
        pagination: { total: 2, limit: 1, offset: 0, hasMore: true },
      })
      .mockResolvedValueOnce({
        data: [
          { id: 2, protocolName: 'B', queryType: 'analysis', result: {}, createdAt: 't2' },
        ],
        pagination: { total: 2, limit: 1, offset: 1, hasMore: false },
      })
    mockedDelete.mockResolvedValue(true)

    const { container, root } = await renderWithClient(
      <MemoryRouter initialEntries={['/history']}>
        <Routes>
          <Route path="/history" element={<History />} />
        </Routes>
      </MemoryRouter>,
    )

    await flushPromises()
    expect(container.textContent).toContain('A')

    const deleteBtn = Array.from(container.querySelectorAll('button')).find((btn) =>
      btn.textContent?.includes('删除'),
    )
    deleteBtn?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()
    expect(mockedDelete).toHaveBeenCalled()

    const nextBtn = Array.from(container.querySelectorAll('button')).find((btn) =>
      btn.textContent?.includes('下一页'),
    )
    nextBtn?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()
    expect(mockedList).toHaveBeenCalledTimes(2)
    expect(container.textContent).toContain('B')

    root.unmount()
    container.remove()
  })
})
