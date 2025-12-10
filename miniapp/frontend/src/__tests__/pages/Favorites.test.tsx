import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import Favorites from '@/pages/Favorites'
import { renderWithClient, flushPromises } from '../test-utils'
import {
  addFavorite,
  deleteFavorite,
  getFavorites,
} from '@/services/favorites'

vi.mock('@/services/favorites', () => ({
  getFavorites: vi.fn(),
  addFavorite: vi.fn(),
  deleteFavorite: vi.fn(),
}))

const mockedGet = getFavorites as unknown as ReturnType<typeof vi.fn>
const mockedAdd = addFavorite as unknown as ReturnType<typeof vi.fn>
const mockedDelete = deleteFavorite as unknown as ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Favorites 页面', () => {
  it('展示收藏并支持新增删除', async () => {
    mockedGet.mockResolvedValue([
      { id: 1, protocolName: 'Aave', protocolType: 'eth', addedAt: 'now' },
    ])
    mockedAdd.mockResolvedValue({
      id: 2,
      protocolName: 'Uni',
      protocolType: null,
      addedAt: 'later',
    })
    mockedDelete.mockResolvedValue(true)

    const { container, root } = await renderWithClient(
      <MemoryRouter initialEntries={['/favorites']}>
        <Routes>
          <Route path="/favorites" element={<Favorites />} />
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
      btn.textContent?.includes('添加收藏'),
    )
    addBtn?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()
    expect(mockedAdd).toHaveBeenCalledWith({ protocolName: 'Uni', protocolType: '' })

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
