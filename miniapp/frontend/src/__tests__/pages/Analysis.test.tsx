import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import Analysis from '@/pages/Analysis'
import { useQuery } from '@tanstack/react-query'

vi.mock('@tanstack/react-query', () => ({
  useQuery: vi.fn(),
}))

const useQueryMock = useQuery as unknown as ReturnType<typeof vi.fn>

beforeEach(() => {
  vi.clearAllMocks()
})

describe('Analysis 页面', () => {
  it('加载完成时展示筛选与协议列表并支持搜索', () => {
    useQueryMock.mockReturnValue({
      data: [
        { id: '1', name: 'Aave', category: 'lending', chain: 'ethereum' },
        { id: '2', name: 'GMX', category: 'derivatives', chain: 'arbitrum' },
      ],
      isLoading: false,
      isError: false,
    })

    render(<Analysis />)

    expect(screen.getByText('协议选择器')).toBeInTheDocument()
    expect(screen.getByText('Aave')).toBeInTheDocument()
    expect(screen.getByText('GMX')).toBeInTheDocument()

    fireEvent.change(screen.getByPlaceholderText('搜索协议'), {
      target: { value: 'zzz' },
    })

    expect(screen.getByText('暂无匹配协议')).toBeInTheDocument()
    expect(useQueryMock).toHaveBeenCalledWith(expect.objectContaining({ queryKey: ['protocols'] }))
  })

  it('加载状态展示提示', () => {
    useQueryMock.mockReturnValue({ data: undefined, isLoading: true, isError: false })
    render(<Analysis />)
    expect(screen.getByText('加载协议列表...')).toBeInTheDocument()
  })

  it('错误状态展示提示', () => {
    useQueryMock.mockReturnValue({ data: undefined, isLoading: false, isError: true })
    render(<Analysis />)
    expect(screen.getByText('加载失败')).toBeInTheDocument()
    expect(screen.getByText('无法获取协议数据')).toBeInTheDocument()
  })
})
