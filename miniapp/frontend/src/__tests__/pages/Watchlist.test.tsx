import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Watchlist from '@/pages/Watchlist'
import { renderWithClient, flushPromises } from '../test-utils'
import {
  batchUpdateWatchlist,
  createWatchlist,
  deleteWatchlist,
  getWatchlist,
  updateWatchlist,
} from '@/services/watchlist'

vi.mock('@/services/watchlist', () => ({
  getWatchlist: vi.fn(),
  createWatchlist: vi.fn(),
  updateWatchlist: vi.fn(),
  deleteWatchlist: vi.fn(),
  batchUpdateWatchlist: vi.fn(),
}))

const mockedGet = getWatchlist as unknown as ReturnType<typeof vi.fn>
const mockedCreate = createWatchlist as unknown as ReturnType<typeof vi.fn>
const mockedUpdate = updateWatchlist as unknown as ReturnType<typeof vi.fn>
const mockedDelete = deleteWatchlist as unknown as ReturnType<typeof vi.fn>
const mockedBatch = batchUpdateWatchlist as unknown as ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Watchlist 页面', () => {
  it('添加、编辑、批量操作', async () => {
    mockedGet.mockResolvedValue([
      {
        id: 1,
        protocolName: 'Aave',
        conditionType: 'tvl_drop',
        threshold: 10,
        isActive: true,
        createdAt: 'now',
        updatedAt: 'now',
      },
    ])
    mockedCreate.mockResolvedValue({
      id: 2,
      protocolName: 'Uni',
      conditionType: 'apy_rise',
      threshold: 5,
      isActive: true,
      createdAt: 'now',
      updatedAt: 'now',
    })
    mockedUpdate.mockResolvedValue({
      id: 1,
      protocolName: 'Aave',
      conditionType: 'tvl_drop',
      threshold: 20,
      isActive: true,
      createdAt: 'now',
      updatedAt: 'now',
    })
    mockedDelete.mockResolvedValue(true)
    mockedBatch.mockResolvedValue(true)

    const { container, root } = await renderWithClient(
      <MemoryRouter initialEntries={['/watchlist']}>
        <Routes>
          <Route path="/watchlist" element={<Watchlist />} />
        </Routes>
      </MemoryRouter>,
    )

    await flushPromises()
    expect(container.textContent).toContain('Aave')

    const inputs = container.querySelectorAll('input')
    const nameInput = inputs[0] as HTMLInputElement
    nameInput.value = 'Uni'
    nameInput.dispatchEvent(new Event('input', { bubbles: true }))

    const addBtn = Array.from(container.querySelectorAll('button')).find((btn) =>
      btn.textContent?.includes('添加监控'),
    )
    addBtn?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()
    expect(mockedCreate).toHaveBeenCalled()

    const batchOffBtn = Array.from(container.querySelectorAll('button')).find((btn) =>
      btn.textContent?.includes('全部关闭'),
    )
    batchOffBtn?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()
    expect(mockedBatch).toHaveBeenCalledWith([1], false)

    const editBtn = Array.from(container.querySelectorAll('button')).find((btn) =>
      btn.textContent?.includes('编辑'),
    )
    editBtn?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()

    const thresholdInput = inputs[1] as HTMLInputElement
    thresholdInput.value = '20'
    thresholdInput.dispatchEvent(new Event('input', { bubbles: true }))

    const saveBtn = Array.from(container.querySelectorAll('button')).find((btn) =>
      btn.textContent?.includes('保存修改'),
    )
    saveBtn?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()
    expect(mockedUpdate).toHaveBeenCalledWith(1, {
      conditionType: 'tvl_drop',
      threshold: 20,
      isActive: true,
      alertMessage: '',
    })

    const deleteBtn = Array.from(container.querySelectorAll('button')).find((btn) =>
      btn.textContent?.includes('删除'),
    )
    deleteBtn?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()
    expect(mockedDelete).toHaveBeenCalledWith(1)

    root.unmount()
    container.remove()
  })
})
