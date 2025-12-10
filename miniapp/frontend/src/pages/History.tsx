import { useEffect, useState } from 'react'
import { useInfiniteQuery, useMutation } from '@tanstack/react-query'
import { Button, ErrorBlock, Input, SearchBar, Selector } from 'antd-mobile'
import HistoryTable from '@/components/HistoryTable'
import { usePagination } from '@/hooks/usePagination'
import {
  deleteAnalysisRecord,
  listAnalysisHistory,
} from '@/services/analysis-history'
import type { Analysis } from '@/types/analysis'
import styles from './Page.module.css'

const History = () => {
  const { page, setPage, limit, setLimit, nextPage, prevPage } = usePagination({
    initialLimit: 10,
  })
  const [protocol, setProtocol] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [queryType, setQueryType] = useState<string | undefined>(undefined)

  const {
    data,
    isLoading,
    isError,
    fetchNextPage,
    isFetchingNextPage,
    refetch,
  } = useInfiniteQuery({
    queryKey: ['analysis-history', protocol, startDate, endDate, queryType, limit],
    initialPageParam: 1,
    queryFn: ({ pageParam }) =>
      listAnalysisHistory({
        page: pageParam,
        limit,
        protocol: protocol || undefined,
        startDate: startDate || undefined,
        endDate: endDate || undefined,
        queryType,
      }),
    getNextPageParam: (lastPage, pages) =>
      lastPage.pagination.hasMore ? pages.length + 1 : undefined,
  })

  const deleteMutation = useMutation({
    mutationFn: (id: number) => deleteAnalysisRecord(id),
    onSuccess: () => refetch(),
  })

  const loadedPages = data?.pages ?? []
  const currentPageData = loadedPages[page - 1]
  const records: Analysis[] = currentPageData?.data ?? []
  const hasMore = loadedPages[loadedPages.length - 1]?.pagination.hasMore ?? false

  useEffect(() => {
    // 重置页码，确保过滤条件变化后从第一页开始
    setPage(1)
  }, [protocol, startDate, endDate, queryType, limit, setPage])

  const handleNext = async () => {
    if (page < loadedPages.length) {
      nextPage()
      return
    }
    if (hasMore) {
      await fetchNextPage()
      nextPage()
    }
  }

  const handleDelete = async (id: number) => {
    await deleteMutation.mutateAsync(id)
  }

  if (isLoading && !isFetchingNextPage) {
    return <HistoryTable records={[]} loading />
  }

  if (isError) {
    return (
      <div className="space-y-2">
        <ErrorBlock status="default" title="加载失败" description="无法获取分析历史" />
        <Button size="small" onClick={() => refetch()}>
          重试
        </Button>
      </div>
    )
  }

  return (
    <div className={`${styles.page} space-y-3`}>
      <div className={`${styles.section} flex flex-col gap-3`}>
        <div className={styles.sectionHeader}>
          <div className={styles.sectionTitle}>筛选器</div>
        </div>
        <SearchBar
          placeholder="按协议搜索"
          value={protocol}
          onChange={setProtocol}
          showCancelButton
        />
        <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
          <Input
            placeholder="开始日期"
            type="date"
            value={startDate}
            onChange={setStartDate}
          />
          <Input placeholder="结束日期" type="date" value={endDate} onChange={setEndDate} />
          <Selector
            options={[
              { label: '全部类型', value: 'all' },
              { label: '分析', value: 'analysis' },
              { label: '对比', value: 'comparison' },
              { label: '推荐', value: 'recommendation' },
            ]}
            value={queryType ? [queryType] : ['all']}
            onChange={(val) => setQueryType(val[0] === 'all' ? undefined : val[0])}
          />
        </div>
      </div>

      <div className={styles.section}>
        <HistoryTable
          records={records}
          loading={isLoading && !currentPageData}
          error={null}
          onDelete={handleDelete}
          onView={() => undefined}
        />
        <div className="mt-3 flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm text-[var(--tg-muted-text)]">
            <span>第 {page} 页</span>
            <Input
              type="number"
              value={String(limit)}
              onChange={(val) => setLimit(Number(val || 10))}
              className="w-20"
            />
            <span>条/页</span>
          </div>
          <div className="flex gap-2">
            <Button size="small" disabled={page === 1} onClick={prevPage}>
              上一页
            </Button>
            <Button
              size="small"
              loading={isFetchingNextPage}
              disabled={!hasMore && page >= loadedPages.length}
              onClick={handleNext}
            >
              下一页
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}

export default History
