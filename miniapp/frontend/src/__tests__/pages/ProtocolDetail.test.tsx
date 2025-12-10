import { beforeEach, describe, expect, it, vi } from 'vitest'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import ProtocolDetail from '@/pages/ProtocolDetail'
import { renderWithClient, flushPromises } from '../test-utils'
import {
  getDetail,
  getMarketData,
  getPools,
  triggerAnalysis,
} from '@/services/protocols'

vi.mock('@/services/protocols', () => ({
  getDetail: vi.fn(),
  getMarketData: vi.fn(),
  getPools: vi.fn(),
  triggerAnalysis: vi.fn(),
}))

const mockedGetDetail = getDetail as unknown as ReturnType<typeof vi.fn>
const mockedGetMarketData = getMarketData as unknown as ReturnType<typeof vi.fn>
const mockedGetPools = getPools as unknown as ReturnType<typeof vi.fn>
const mockedTrigger = triggerAnalysis as unknown as ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.clearAllMocks()
})

describe('ProtocolDetail 页面', () => {
  it('展示协议详情并触发分析', async () => {
    mockedGetDetail.mockResolvedValue({
      id: 'aave',
      name: 'Aave',
      description: 'Lending',
      chain: 'eth',
      tvl: 1000,
      apy: 4,
    })
    mockedGetMarketData.mockResolvedValue({
      price: 10,
      marketCap: 1000000,
      volume24h: 5000,
      change24h: 1,
    })
    mockedGetPools.mockResolvedValue([
      { id: '1', name: 'Pool', chain: 'eth', tvl: 100, apy: 3 },
    ])
    mockedTrigger.mockResolvedValue({ record_id: 1, status: 'queued', protocol: 'aave' })

    const { container, root } = await renderWithClient(
      <MemoryRouter initialEntries={['/protocols/aave']}>
        <Routes>
          <Route path="/protocols/:slug" element={<ProtocolDetail />} />
        </Routes>
      </MemoryRouter>,
    )

    await flushPromises()

    expect(container.textContent).toContain('Aave')
    expect(container.textContent).toContain('TVL')

    const triggerButton = Array.from(container.querySelectorAll('button')).find((btn) =>
      btn.textContent?.includes('触发分析'),
    )
    triggerButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    await flushPromises()
    expect(mockedTrigger).toHaveBeenCalled()

    root.unmount()
    container.remove()
  })
})
